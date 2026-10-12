import asyncio
from pathlib import Path
import edge_tts
from app.config import AUDIO_DIR, VOICES, RATE_MAP, TTS_PROXY


def audio_path(sentence_id: int, rate: float) -> Path:
    return AUDIO_DIR / f"{sentence_id}_{rate}.mp3"


def _is_valid(p: Path) -> bool:
    """有效缓存 = 文件存在且非空（edge-tts 失败时可能留下 0 字节文件）。"""
    return p.exists() and p.stat().st_size > 0


async def _synth(text: str, voice: str, rate_pct: str, out: Path, proxy: str | None):
    await edge_tts.Communicate(text, voice, rate=rate_pct, proxy=proxy).save(str(out))


def synthesize(sentence_id: int, text: str, voice_key: str = "aria", rate: float = 1.0) -> Path:
    """同步封装：合成并缓存 mp3。voice_key: aria/guy 或完整声音名。"""
    voice = VOICES.get(voice_key, voice_key)
    if voice not in VOICES.values():
        voice = VOICES["aria"]
    out = audio_path(sentence_id, rate)
    # 空文件不算缓存成功，删掉重新合成
    if _is_valid(out):
        return out
    out.unlink(missing_ok=True)
    rate_pct = RATE_MAP.get(rate, "+0%")
    proxy = TTS_PROXY or None
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            asyncio.run(_synth(text, voice, rate_pct, out, proxy))
            if _is_valid(out):
                return out
            # 合成"成功"但产物为空（网络中断常见），当作失败重试
            out.unlink(missing_ok=True)
            raise RuntimeError("TTS 返回了空音频")
        except Exception as e:
            out.unlink(missing_ok=True)
            last_err = e
            if attempt == 2:
                break
    raise RuntimeError(f"音频合成失败（{type(last_err).__name__}），"
                       f"edge-tts 需要能访问微软服务；若提示 403 拦截，"
                       f"请开启代理客户端并设置 TTS_PROXY 后重试")


def remove_audio(sentence_id: int):
    for pattern in (f"{sentence_id}_*.wav", f"{sentence_id}_*.mp3"):
        for p in AUDIO_DIR.glob(pattern):
            p.unlink(missing_ok=True)
