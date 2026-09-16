from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Difficulty(Base):
    __tablename__ = "difficulty_levels"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    ielts: Mapped[str] = mapped_column(String(16))
    cefr: Mapped[str] = mapped_column(String(8))
    label: Mapped[str] = mapped_column(String(32))

    sentences = relationship("Sentence", back_populates="difficulty")


class Sentence(Base):
    __tablename__ = "sentences"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text, unique=True)
    translation: Mapped[str] = mapped_column(Text, default="")
    difficulty_code: Mapped[str] = mapped_column(String(8), ForeignKey("difficulty_levels.code"))
    topic: Mapped[str] = mapped_column(String(64), default="general")
    voice: Mapped[str] = mapped_column(String(32), default="en-US-AriaNeural")
    has_audio: Mapped[bool] = mapped_column(Boolean, default=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utcnow)

    difficulty = relationship("Difficulty", back_populates="sentences")


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentences.id", ondelete="CASCADE"))
    correct: Mapped[int] = mapped_column(Integer)
    chosen_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
