import asyncio
from pathlib import Path
import edge_tts
from app.config import AUDIO_DIR, VOICES, RATE_MAP


def audio_path(sentence_id: int, rate: float) -> Path:
    return AUDIO_DIR / f"{sentence_id}_{rate}.mp3"


async def _synth(text: str, voice: str, rate_pct: str, out: Path):
    await edge_tts.Communicate(text, voice, rate=rate_pct).save(str(out))


def synthesize(sentence_id: int, text: str, voice_key: str = "aria", rate: float = 1.0) -> Path:
    """同步封装：合成并缓存 mp3。voice_key: aria/guy 或完整声音名。"""
    voice = VOICES.get(voice_key, voice_key)
    if voice not in VOICES.values():
        voice = VOICES["aria"]
    out = audio_path(sentence_id, rate)
    if out.exists():
        return out
    rate_pct = RATE_MAP.get(rate, "+0%")
    for attempt in range(3):
        try:
            asyncio.run(_synth(text, voice, rate_pct, out))
            return out
        except Exception:
            if attempt == 2:
                raise
    return out


def remove_audio(sentence_id: int):
    for p in AUDIO_DIR.glob(f"{sentence_id}_*.mp3"):
        p.unlink(missing_ok=True)
