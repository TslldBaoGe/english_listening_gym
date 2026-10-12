import time
import wave
from pathlib import Path

from piper import PiperVoice
from piper.config import SynthesisConfig

from app.config import AUDIO_DIR

# 语音模型（离线，无需联网）：backend/data/piper/*.onnx
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "piper"

# 前端声音 -> 模型文件（high 音质）
VOICE_MODELS = {
    "aria": "en_US-ljspeech-high.onnx",            # 女声
    "guy": "en_US-ryan-high.onnx",                 # 男声
    # 历史数据里存的是完整声音名，这里兼容
    "en-US-AriaNeural": "en_US-ljspeech-high.onnx",
    "en-US-GuyNeural": "en_US-ryan-high.onnx",
}

# 前端语速 -> piper length_scale（值越大念得越慢）
LENGTH_SCALE = {1.0: 1.0, 0.85: 1.1, 0.75: 1.25, 0.5: 1.6}

_voices = {}   # model_file -> PiperVoice（进程内各加载一次，约 1~2 秒）


def _get_voice(voice_key: str) -> PiperVoice:
    """惰性加载模型：每个声音整个后端进程只加载一次。"""
    model_file = VOICE_MODELS.get(voice_key, VOICE_MODELS["aria"])
    if model_file not in _voices:
        _voices[model_file] = PiperVoice.load(str(MODEL_DIR / model_file))
    return _voices[model_file]


def audio_path(sentence_id: int, rate: float, voice_key: str = "aria") -> Path:
    # 不同声音分开缓存，避免同句互顶
    return AUDIO_DIR / f"{sentence_id}_{voice_key}_{rate}.wav"


def _is_valid(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 44   # 至少要有 wav 头


def synthesize(sentence_id: int, text: str, voice_key: str = "aria", rate: float = 1.0) -> Path:
    """本地离线合成 WAV。不联网，无配额，无审查。"""
    voice_key = voice_key if voice_key in VOICE_MODELS else "aria"
    out = audio_path(sentence_id, rate, voice_key)
    if _is_valid(out):
        return out
    out.unlink(missing_ok=True)

    t0 = time.time()
    try:
        length_scale = LENGTH_SCALE.get(rate, 1.0)
        syn_config = SynthesisConfig(length_scale=length_scale)
        # high 模型输出：22050Hz 单声道 16bit
        with wave.open(str(out), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            _get_voice(voice_key).synthesize_wav(text, wf, syn_config=syn_config, set_wav_format=False)
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
