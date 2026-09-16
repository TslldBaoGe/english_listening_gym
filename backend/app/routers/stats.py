from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Sentence, Attempt

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats(db: Session = Depends(get_db)):
    total_sentences = db.scalar(select(func.count(Sentence.id)))
    by_difficulty = dict(db.execute(
        select(Sentence.difficulty_code, func.count(Sentence.id))
        .group_by(Sentence.difficulty_code)).all())
    total_attempts = db.scalar(select(func.count(Attempt.id))) or 0
    correct_attempts = db.scalar(
        select(func.count(Attempt.id)).where(Attempt.correct == 1)) or 0
    since = datetime.now(timezone.utc) - timedelta(days=7)
    recent = db.execute(
        select(func.date(Attempt.created_at), func.count(Attempt.id),
               func.sum(Attempt.correct))
        .where(Attempt.created_at >= since)
        .group_by(func.date(Attempt.created_at))).all()
    worst = db.scalars(
        select(Sentence).where(Sentence.wrong_count > 0)
        .order_by(Sentence.wrong_count.desc()).limit(10)).all()
    return {
        "total_sentences": total_sentences,
        "by_difficulty": by_difficulty,
        "total_attempts": total_attempts,
        "correct_rate": round(correct_attempts / total_attempts, 3) if total_attempts else None,
        "recent_7days": [{"date": str(d), "count": c, "correct": int(s or 0)}
                          for d, c, s in recent],
        "worst_sentences": [{"id": s.id, "text": s.text, "translation": s.translation,
                             "wrong_count": s.wrong_count} for s in worst],
    }
