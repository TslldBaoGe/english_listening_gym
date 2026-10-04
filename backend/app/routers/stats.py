from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session
from app.config import DIFFICULTIES
from app.db.database import get_db
from app.db.models import Sentence, Attempt

router = APIRouter(prefix="/api/stats", tags=["stats"])

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _by_difficulty(db: Session) -> list[dict]:
    """每个难度的 总数 / 已掌握 / 错题数，按 L1→L5 排好（没有句子的难度也列出来）。"""
    rows = db.execute(
        select(Sentence.difficulty_code,
               func.count(Sentence.id),
               func.sum(case((Sentence.mastered.is_(True), 1), else_=0)),
               func.sum(case((Sentence.wrong_count > 0, 1), else_=0)))
        .group_by(Sentence.difficulty_code)).all()
    agg = {code: (int(cnt or 0), int(ms or 0), int(wr or 0)) for code, cnt, ms, wr in rows}
    out = []
    for d in DIFFICULTIES:
        cnt, ms, wr = agg.pop(d["code"], (0, 0, 0))
        out.append({"code": d["code"], "label": d["label"], "ielts": d["ielts"],
                    "cefr": d["cefr"], "count": cnt, "mastered": ms, "wrong": wr})
    for code, (cnt, ms, wr) in sorted(agg.items()):   # 配置里没有的难度码兜底
        out.append({"code": code, "label": "", "ielts": "", "cefr": "",
                    "count": cnt, "mastered": ms, "wrong": wr})
    return out


def _recent_7days(db: Session) -> list[dict]:
    """最近 7 天练习量，按服务器本地日期分桶（created_at 存的是 UTC），没有练习的天补 0。"""
    local_tz = datetime.now().astimezone().tzinfo
    today = datetime.now(local_tz).date()
    days = {today - timedelta(days=i): {"count": 0, "correct": 0} for i in range(6, -1, -1)}
    earliest = datetime.now(timezone.utc) - timedelta(days=8)
    rows = db.execute(select(Attempt.created_at, Attempt.correct)
                      .where(Attempt.created_at >= earliest)).all()
    for created, correct in rows:
        if created is None:
            continue
        if created.tzinfo is None:          # SQLite 取出来是裸时间，按 UTC 解释
            created = created.replace(tzinfo=timezone.utc)
        day = created.astimezone(local_tz).date()
        if day in days:
            days[day]["count"] += 1
            days[day]["correct"] += int(correct or 0)
    return [{"date": d.isoformat(), "weekday": WEEKDAYS[d.weekday()], "is_today": d == today,
             "count": v["count"], "correct": v["correct"]} for d, v in sorted(days.items())]


@router.get("")
def stats(db: Session = Depends(get_db)):
    total_sentences = db.scalar(select(func.count(Sentence.id))) or 0
    mastered_sentences = db.scalar(
        select(func.count(Sentence.id)).where(Sentence.mastered.is_(True))) or 0
    wrong_total = db.scalar(
        select(func.count(Sentence.id)).where(Sentence.wrong_count > 0)) or 0
    total_attempts = db.scalar(select(func.count(Attempt.id))) or 0
    correct_attempts = db.scalar(
        select(func.count(Attempt.id)).where(Attempt.correct == 1)) or 0
    studied = db.scalar(select(func.count(Sentence.id)).where(Sentence.total_count > 0)) or 0
    worst = db.scalars(
        select(Sentence).where(Sentence.wrong_count > 0)
        .order_by(Sentence.wrong_count.desc(), Sentence.id).limit(10)).all()
    return {
        "total_sentences": total_sentences,
        "mastered_sentences": mastered_sentences,
        "wrong_total": wrong_total,
        "studied_sentences": studied,
        "by_difficulty": _by_difficulty(db),
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "correct_rate": round(correct_attempts / total_attempts, 3) if total_attempts else None,
        "recent_7days": _recent_7days(db),
        "worst_sentences": [{"id": s.id, "text": s.text, "translation": s.translation,
                             "difficulty_code": s.difficulty_code,
                             "wrong_count": s.wrong_count} for s in worst],
    }


@router.delete("/wrong/{sentence_id}")
def delete_wrong(sentence_id: int, db: Session = Depends(get_db)):
    """把一道题移出错题本：错误次数清零。

    句子本身、音频、向量都保留在知识库里（要彻底删除请用 04 知识库的删除）。
    """
    s = db.get(Sentence, sentence_id)
    if not s:
        raise HTTPException(404, "句子不存在")
    s.wrong_count = 0
    db.commit()
    return {"ok": True, "id": sentence_id}
