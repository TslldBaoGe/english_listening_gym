import os
import time
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import AUDIO_DIR

# TTS 提供方：kokoro（本地离线，默认）| edge（微软云端，需可直连或开代理）
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "kokoro")
# edge 提供方专用的代理开关（kokoro 不需要联网）
TTS_PROXY = os.getenv("TTS_PROXY", "")

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "kokoro"
KOKORO_MODEL = MODEL_DIR / "kokoro-v1_0.pth"
KOKORO_CONFIG = MODEL_DIR / "config.json"
KOKORO_VOICES = {
    # 全部女声音色（前端下拉可选）
    "af_heart": MODEL_DIR / "voices" / "af_heart.pt",
    "af_bella": MODEL_DIR / "voices" / "af_bella.pt",
    "af_nicole": MODEL_DIR / "voices" / "af_nicole.pt",
    "af_aoede": MODEL_DIR / "voices" / "af_aoede.pt",
    "af_kore": MODEL_DIR / "voices" / "af_kore.pt",
    "af_sarah": MODEL_DIR / "voices" / "af_sarah.pt",
    "af_nova": MODEL_DIR / "voices" / "af_nova.pt",
    "af_sky": MODEL_DIR / "voices" / "af_sky.pt",
    "af_alloy": MODEL_DIR / "voices" / "af_alloy.pt",
    "af_jessica": MODEL_DIR / "voices" / "af_jessica.pt",
    "af_river": MODEL_DIR / "voices" / "af_river.pt",
    "bf_emma": MODEL_DIR / "voices" / "bf_emma.pt",
    "bf_isabella": MODEL_DIR / "voices" / "bf_isabella.pt",
    "bf_alice": MODEL_DIR / "voices" / "bf_alice.pt",
    "bf_lily": MODEL_DIR / "voices" / "bf_lily.pt",
    # 历史数据兼容：旧记录里存的是 aria/guy 或完整声音名
    "aria": MODEL_DIR / "voices" / "af_heart.pt",
    "guy": MODEL_DIR / "voices" / "af_heart.pt",
    "en-US-AriaNeural": MODEL_DIR / "voices" / "af_heart.pt",
    "en-US-GuyNeural": MODEL_DIR / "voices" / "af_heart.pt",
}

# 音色文件缺失检查（服务器上需确保全部 .pt 已就位）
import os as _os
_missing = [k for k, p in KOKORO_VOICES.items() if not _os.path.exists(p)]
if _missing:
    import logging
    logging.getLogger(__name__).warning("缺少音色文件: %s", _missing)

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
    _normalize_loudness(out)
    return out


def _normalize_loudness(p: Path):
    """响度压缩：RMS 拉到目标响度（约 -13 dBFS，明显响亮），
    峰值用 tanh 软限幅压住，既响又不刺耳不失真。"""
    data, sr = sf.read(str(p))
    if data.size == 0:
        return
    data = data.astype('float64')
    rms = float(np.sqrt(np.mean(data ** 2)))
    if rms < 1e-4:
        return
    target_rms = 0.22                                    # 约 -13 dBFS
    gain = min(target_rms / rms, 20.0)
    out = np.tanh(data * gain)                           # 软限幅：低电平近似线性，峰值被柔压
    sf.write(str(p), out, sr)


def remove_audio(sentence_id: int):
    for pattern in (f"{sentence_id}_*.wav", f"{sentence_id}_*.mp3"):
        for p in AUDIO_DIR.glob(pattern):
            p.unlink(missing_ok=True)
