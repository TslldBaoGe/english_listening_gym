from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import get_db
from app.db.models import Sentence
from app.services import tts

router = APIRouter(prefix="/api/audio", tags=["audio"])

ALLOWED_RATES = {1.0, 0.85, 0.75, 0.5}


@router.get("/{sentence_id}")
def get_audio(sentence_id: int, rate: float = 1.0, db: Session = Depends(get_db)):
    s = db.get(Sentence, sentence_id)
    if not s:
        raise HTTPException(404, "句子不存在")
    rate = rate if rate in ALLOWED_RATES else 1.0
    try:
        path = tts.synthesize(sentence_id, s.text, s.voice, rate)
    except Exception:
        raise HTTPException(502, "音频合成失败，请稍后重试")
    return FileResponse(path, media_type="audio/mpeg")
