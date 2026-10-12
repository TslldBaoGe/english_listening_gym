import os
import time
import wave
from pathlib import Path

from app.config import AUDIO_DIR

# TTS 提供方：kokoro（本地离线，默认）| edge（微软云端，需可直连或开代理）
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "kokoro")
# edge 提供方专用的代理开关（kokoro 不需要联网）
TTS_PROXY = os.getenv("TTS_PROXY", "")

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "kokoro"
KOKORO_MODEL = MODEL_DIR / "kokoro-v1_0.pth"
KOKORO_CONFIG = MODEL_DIR / "config.json"
KOKORO_VOICES = {
    "aria": MODEL_DIR / "voices" / "af_heart.pt",      # 女声
    "guy": MODEL_DIR / "voices" / "am_michael.pt",     # 男声
    # 历史数据里存的是完整声音名，这里兼容
    "en-US-AriaNeural": MODEL_DIR / "voices" / "af_heart.pt",
    "en-US-GuyNeural": MODEL_DIR / "voices" / "am_michael.pt",
}

# 前端语速 -> kokoro speed
KOKORO_SPEED = {1.0: 1.0, 0.85: 0.8, 0.75: 0.65, 0.5: 0.45}

_pipeline = None


def _get_pipeline():
    """惰性加载 kokoro 管线：整个后端进程只加载一次（约 2~4 秒）。"""
    global _pipeline
    if _pipeline is None:
        # 禁止 huggingface_hub 联网：模型/音色/配置全部本地化
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        from kokoro import KPipeline, KModel
        km = KModel(repo_id="hexgrad/Kokoro-82M",
                    config=str(KOKORO_CONFIG), model=str(KOKORO_MODEL))
        _pipeline = KPipeline(lang_code="a", model=km)
    return _pipeline


def audio_path(sentence_id: int, rate: float) -> Path:
    return AUDIO_DIR / f"{sentence_id}_{rate}.wav"


def _is_valid(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 44


def _synth_kokoro(text: str, voice_key: str, rate: float, out: Path):
    voice_path = KOKORO_VOICES.get(voice_key, KOKORO_VOICES["aria"])
    speed = KOKORO_SPEED.get(rate, 1.0)
    pipe = _get_pipeline()
    import soundfile as sf
    audio = None
    for _gs, _ps, audio in pipe(text, voice=str(voice_path), speed=speed):
        pass   # 长句会分块，取最后一块，前面的自然衔接
    # kokoro 固定输出 24000Hz
    sf.write(str(out), audio.detach().cpu().numpy(), 24000)


def _synth_edge(text: str, voice_key: str, rate: float, out: Path):
    import asyncio
    import edge_tts
    from app.config import VOICES, RATE_MAP
    voice = VOICES.get(voice_key, voice_key)
    if voice not in VOICES.values():
        voice = VOICES["aria"]
    asyncio.run(edge_tts.Communicate(
        text, voice, rate=RATE_MAP.get(rate, "+0%"), proxy=TTS_PROXY or None
    ).save(str(out)))


def synthesize(sentence_id: int, text: str, voice_key: str = "aria", rate: float = 1.0) -> Path:
    out = audio_path(sentence_id, rate)
    if _is_valid(out):
        return out
    out.unlink(missing_ok=True)

    t0 = time.time()
    try:
        if TTS_PROVIDER == "edge":
            _synth_edge(text, voice_key, rate, out)
        else:
            _synth_kokoro(text, voice_key, rate, out)
    except Exception:
        out.unlink(missing_ok=True)
        raise

    if not _is_valid(out):
        out.unlink(missing_ok=True)
        raise RuntimeError("TTS 产物为空")
    return out


def remove_audio(sentence_id: int):
    for pattern in (f"{sentence_id}_*.wav", f"{sentence_id}_*.mp3"):
        for p in AUDIO_DIR.glob(pattern):
            p.unlink(missing_ok=True)
