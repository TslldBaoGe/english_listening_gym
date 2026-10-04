from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func
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
    # 把同难度同主题已有的句子作为「禁用清单」交给 LLM，避免它反复生成雷同句被去重拦掉
    avoid = [s.text for s in db.scalars(
        select(Sentence)
        .where(Sentence.difficulty_code == body.difficulty, Sentence.topic == body.topic)
        .order_by(Sentence.id.desc()).limit(20)).all()]
    while remaining > 0 and retries < 6:
        try:
            items = llm.generate_sentences(body.difficulty, body.topic, remaining,
                                           avoid=avoid, attempt=retries)
        except Exception as e:
            raise HTTPException(502, f"生成失败: {e}")
        for it in items:
            text = str(it.get("text", "")).strip()
            if not text:
                continue
            if _is_duplicate(text, db):
                dup_blocked += 1
                retries += 1
                avoid.append(text)   # 这一轮已被否掉的句子，下一轮也让 LLM 避开
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
                409, f"生成的内容与知识库中已有句子过于相似（同义或换词模板句），"
                     f"已拦截 {dup_blocked} 句。该主题下句子可能已经比较全了 —— "
                     "换个主题、换个难度，或先把主题描述写具体一点（如 daily life → morning routine）"
                     "通常就能立刻生成成功。")
        raise HTTPException(502, "生成失败，请重试")
    return {"sentences": results}


@router.get("")
def list_sentences(page: int = 1, size: int = 20, difficulty: str | None = None,
                   topic: str | None = None, keyword: str | None = None,
                   mastered: bool | None = None,
                   db: Session = Depends(get_db)):
    q = select(Sentence).order_by(Sentence.id.desc())
    if difficulty:
        q = q.where(Sentence.difficulty_code == difficulty)
    if topic:
        q = q.where(Sentence.topic == topic)
    if keyword:
        q = q.where(Sentence.text.contains(keyword))
    if mastered is not None:
        q = q.where(Sentence.mastered == mastered)
    total = len(db.scalars(q).all())
    rows = db.scalars(q.offset((page - 1) * size).limit(size)).all()
    return {"total": total, "items": [
        {"id": s.id, "text": s.text, "translation": s.translation,
         "difficulty": s.difficulty_code, "topic": s.topic,
         "wrong_count": s.wrong_count, "total_count": s.total_count,
         "mastered": bool(s.mastered),
         "audio_url": f"/api/audio/{s.id}"} for s in rows]}


class MasteredIn(BaseModel):
    mastered: bool = True


@router.post("/{sentence_id}/mastered")
def set_mastered(sentence_id: int, body: MasteredIn, db: Session = Depends(get_db)):
    """标记/取消「已掌握」：已掌握的句子不会再被测验抽到。"""
    s = db.get(Sentence, sentence_id)
    if not s:
        raise HTTPException(404, "句子不存在")
    s.mastered = body.mastered
    db.commit()
    return {"ok": True, "id": sentence_id, "mastered": bool(s.mastered)}


@router.get("/random")
def random_sentences(count: int = 1, difficulty: str | None = None,
                     include_mastered: bool = False,
                     db: Session = Depends(get_db)):
    """测验用：从知识库随机抽句（默认跳过已答对的）。"""
    q = select(Sentence).order_by(func.random())
    if difficulty:
        q = q.where(Sentence.difficulty_code == difficulty)
    if not include_mastered:
        q = q.where(Sentence.mastered == False)  # noqa: E712
    rows = db.scalars(q.limit(max(1, min(count, 5)))).all()
    if not rows:
        def _count(extra=None) -> int:
            cq = select(func.count(Sentence.id))
            if difficulty:
                cq = cq.where(Sentence.difficulty_code == difficulty)
            if extra is not None:
                cq = cq.where(extra)
            return db.scalar(cq) or 0

        total, done = _count(), _count(Sentence.mastered == True)  # noqa: E712
        if total and done >= total and not include_mastered:
            raise HTTPException(
                404, f"这 {total} 句都已经答对了（已掌握）。想再练一遍就勾上"
                     "「包含已掌握的」，或者到 04 知识库点「重新加入测验」。")
        raise HTTPException(404, "知识库为空（或该难度下没有句子），请先生成句子")
    return {"sentences": [
        {"id": s.id, "text": s.text, "translation": s.translation,
         "difficulty": s.difficulty_code, "topic": s.topic,
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
