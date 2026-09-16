import random
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.database import get_db
from app.db.models import Sentence
from app.services import llm
from app.services import quiz_engine
from app.services import distractors as local_distractors
from app.services.text_utils import normalize
from app.config import QUIZ_SESSION_TTL

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# quiz_id -> {sentence_id, answer, options, expires}
_sessions: dict[str, dict] = {}
# sentence_id -> 已生成的干扰项（避免每次抽题都调 LLM）
_distractor_cache: dict[int, list[str]] = {}


def _clean(cands, answer: str) -> list[str]:
    """丢弃空值、与原文相同的项，并去重。"""
    target = normalize(answer)
    out = []
    for c in cands:
        c = str(c or "").strip()
        if not c or normalize(c) == target:
            continue
        if any(normalize(c) == normalize(x) for x in out):
            continue
        out.append(c)
    return out


def _cleanup():
    now = time.time()
    for k in [k for k, v in _sessions.items() if v["expires"] < now]:
        _sessions.pop(k, None)


class SubmitIn(BaseModel):
    quiz_id: str
    chosen_text: str


@router.get("/next")
def next_question(difficulty: str | None = None, topic: str | None = None,
                  db: Session = Depends(get_db)):
    _cleanup()
    s = quiz_engine.pick_next(db, difficulty, topic)
    if not s:
        raise HTTPException(404, "知识库为空，请先生成句子")

    # 1) 优先用缓存的 LLM 干扰项，其次重新调 LLM
    distractors = _distractor_cache.get(s.id)
    if not distractors:
        try:
            distractors = _clean(llm.generate_distractors(s.text, s.topic), s.text)
        except Exception:
            distractors = []
        if len(distractors) >= 3:
            _distractor_cache[s.id] = distractors

    # 2) 库内其他句子兜底
    others = db.scalars(
        select(Sentence).where(Sentence.id != s.id)
        .order_by(func.random()).limit(6)).all()
    pool = [o.text for o in others]
    distractors = _clean(distractors + pool, s.text)[:3]

    # 3) 仍不足则用本地规则生成，保证测验永远能出题
    if len(distractors) < 3:
        distractors = _clean(
            distractors + local_distractors.make_distractors(s.text, pool, 3 - len(distractors)),
            s.text)[:3]

    if not distractors:
        raise HTTPException(502, "无法生成选项，请重试")

    options = distractors + [s.text]
    random.shuffle(options)
    quiz_id = uuid.uuid4().hex
    _sessions[quiz_id] = {"sentence_id": s.id, "answer": s.text,
                          "expires": time.time() + QUIZ_SESSION_TTL}
    return {"quiz_id": quiz_id, "options": options,
            "audio_url": f"/api/audio/{s.id}",
            "difficulty": s.difficulty_code, "topic": s.topic}


@router.post("/submit")
def submit(body: SubmitIn, db: Session = Depends(get_db)):
    sess = _sessions.pop(body.quiz_id, None)
    if not sess:
        raise HTTPException(404, "测验已过期，请重新抽题")
    s = db.get(Sentence, sess["sentence_id"])
    if not s:
        raise HTTPException(404, "句子不存在")
    correct = body.chosen_text.strip() == sess["answer"]
    quiz_engine.record_attempt(db, s, correct, body.chosen_text)
    return {"correct": correct, "original": s.text, "translation": s.translation,
            "wrong_count": s.wrong_count, "total_count": s.total_count}
