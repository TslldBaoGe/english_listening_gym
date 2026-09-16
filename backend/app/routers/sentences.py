from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Sentence
from app.db import vector_store
from app.services import llm, tts
from app.services.text_utils import similarity
from app.config import DUP_DISTANCE, DUP_TEXT_SIM, VOICES

router = APIRouter(prefix="/api/sentences", tags=["sentences"])


def _is_duplicate(text: str, db) -> bool:
    """向量近似 或 词面高度相似，都算重复。"""
    if vector_store.is_duplicate(text, DUP_DISTANCE):
        return True
    existing = db.scalars(select(Sentence.text)).all()
    return any(similarity(text, t) >= DUP_TEXT_SIM for t in existing)


class GenerateIn(BaseModel):
    difficulty: str = "L1"
    topic: str = "daily life"
    count: int = 1
    voice: str = "aria"


@router.post("/generate")
def generate(body: GenerateIn, db: Session = Depends(get_db)):
    results = []
    remaining = max(1, min(body.count, 3))
    retries = 0
    dup_blocked = 0
    while remaining > 0 and retries < 4:
        try:
            items = llm.generate_sentences(body.difficulty, body.topic, remaining)
        except Exception as e:
            raise HTTPException(502, f"生成失败: {e}")
        for it in items:
            text = str(it.get("text", "")).strip()
            if not text:
                continue
            if _is_duplicate(text, db):
                dup_blocked += 1
                retries += 1
                continue
            s = Sentence(text=text, translation=str(it.get("translation", "")),
                         difficulty_code=body.difficulty, topic=body.topic,
                         voice=VOICES.get(body.voice, VOICES["aria"]))
            db.add(s)
            db.commit()
            vector_store.add(s.id, s.text, s.difficulty_code, s.topic)
            try:
                tts.synthesize(s.id, s.text, body.voice, 1.0)
                s.has_audio = True
                db.commit()
            except Exception:
                pass
            results.append({"id": s.id, "text": s.text, "translation": s.translation,
                            "difficulty": s.difficulty_code, "topic": s.topic,
                            "audio_url": f"/api/audio/{s.id}"})
            remaining -= 1
        if remaining > 0:
            retries += 1
    if not results:
        if dup_blocked:
            raise HTTPException(
                409, "生成的内容与知识库中已有句子过于相似（同义或换词模板句），"
                     "已全部拦截。请更换主题或稍后重试。")
        raise HTTPException(502, "生成失败，请重试")
    return {"sentences": results}


@router.get("")
def list_sentences(page: int = 1, size: int = 20, difficulty: str | None = None,
                   topic: str | None = None, keyword: str | None = None,
                   db: Session = Depends(get_db)):
    q = select(Sentence).order_by(Sentence.id.desc())
    if difficulty:
        q = q.where(Sentence.difficulty_code == difficulty)
    if topic:
        q = q.where(Sentence.topic == topic)
    if keyword:
        q = q.where(Sentence.text.contains(keyword))
    total = len(db.scalars(q).all())
    rows = db.scalars(q.offset((page - 1) * size).limit(size)).all()
    return {"total": total, "items": [
        {"id": s.id, "text": s.text, "translation": s.translation,
         "difficulty": s.difficulty_code, "topic": s.topic,
         "wrong_count": s.wrong_count, "total_count": s.total_count,
         "audio_url": f"/api/audio/{s.id}"} for s in rows]}


@router.delete("/{sentence_id}")
def delete(sentence_id: int, db: Session = Depends(get_db)):
    s = db.get(Sentence, sentence_id)
    if not s:
        raise HTTPException(404, "句子不存在")
    db.delete(s)
    db.commit()
    vector_store.remove(sentence_id)
    tts.remove_audio(sentence_id)
    return {"ok": True}
