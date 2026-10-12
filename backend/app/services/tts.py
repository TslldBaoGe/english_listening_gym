import time
import wave
from pathlib import Path

from piper import PiperVoice
from piper.config import SynthesisConfig

from app.config import AUDIO_DIR, VOICES

# 语音模型（离线，无需联网）：backend/data/piper/*.onnx
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "piper"
MODEL_PATH = MODEL_DIR / "en_US-lessac-medium.onnx"

# 声音名仅用于接口兼容（aria/guy 都映射到同一个本地模型）
DEFAULT_VOICE = "en-US-AriaNeural"

# 前端语速 -> piper length_scale（值越大念得越慢）
LENGTH_SCALE = {1.0: 1.0, 0.85: 1.1, 0.75: 1.25, 0.5: 1.6}

_voice = None


def _get_voice() -> PiperVoice:
    """惰性加载模型：整个后端进程只加载一次（约 1.2 秒）。"""
    global _voice
    if _voice is None:
        _voice = PiperVoice.load(str(MODEL_PATH))
    return _voice


def audio_path(sentence_id: int, rate: float) -> Path:
    return AUDIO_DIR / f"{sentence_id}_{rate}.wav"


def _is_valid(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 44   # 至少要有 wav 头


def synthesize(sentence_id: int, text: str, voice_key: str = "aria", rate: float = 1.0) -> Path:
    """本地离线合成 WAV。不联网，无配额，无审查。"""
    out = audio_path(sentence_id, rate)
    if _is_valid(out):
        return out
    out.unlink(missing_ok=True)

    t0 = time.time()
    try:
        length_scale = LENGTH_SCALE.get(rate, 1.0)
        syn_config = SynthesisConfig(length_scale=length_scale)
        # lessac-medium 模型输出：22050Hz 单声道 16bit
        with wave.open(str(out), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            _get_voice().synthesize_wav(text, wf, syn_config=syn_config, set_wav_format=False)
    except Exception:
        out.unlink(missing_ok=True)
        raise

    if not _is_valid(out):
        out.unlink(missing_ok=True)
        raise RuntimeError("本地 TTS 产物为空")
    return out


def remove_audio(sentence_id: int):
    for pattern in (f"{sentence_id}_*.wav", f"{sentence_id}_*.mp3"):
        for p in AUDIO_DIR.glob(pattern):
            p.unlink(missing_ok=True)
