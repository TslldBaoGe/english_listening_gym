import random
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Sentence, Attempt


def pick_next(db: Session, difficulty: str | None = None, topic: str | None = None) -> Sentence | None:
    q = select(Sentence)
    if difficulty:
        q = q.where(Sentence.difficulty_code == difficulty)
    if topic:
        q = q.where(Sentence.topic == topic)
    rows = db.scalars(q).all()
    if not rows:
        return None
    now = datetime.now(timezone.utc)
    weights = []
    for s in rows:
        w = 1.0 + 2.0 * s.wrong_count
        if s.last_reviewed_at:
            days = max((now - s.last_reviewed_at.replace(tzinfo=timezone.utc)).days, 0)
            w += days * 0.5
        else:
            w += 3.0  # 从未考过
        weights.append(w)
    return random.choices(rows, weights=weights, k=1)[0]


def record_attempt(db: Session, sentence: Sentence, correct: bool, chosen: str):
    db.add(Attempt(sentence_id=sentence.id, correct=int(correct), chosen_text=chosen))
    sentence.total_count += 1
    if not correct:
        sentence.wrong_count += 1
    sentence.last_reviewed_at = datetime.now(timezone.utc)
    db.commit()
