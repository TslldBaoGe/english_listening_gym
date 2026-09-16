from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.db import models  # noqa: F401 确保建表
from app.config import DIFFICULTIES, VOICES
from app.routers import sentences, quiz, audio, stats, settings

app = FastAPI(title="English Listening Trainer")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for r in (sentences.router, quiz.router, audio.router, stats.router, settings.router):
    app.include_router(r)


@app.on_event("startup")
def init_db():
    Base.metadata.create_all(engine)
    from app.db.database import SessionLocal
    from app.db.models import Difficulty
    db = SessionLocal()
    try:
        for d in DIFFICULTIES:
            exists = db.query(Difficulty).filter_by(code=d["code"]).first()
            if not exists:
                db.add(Difficulty(code=d["code"], ielts=d["ielts"],
                                  cefr=d["cefr"], label=d["label"]))
        db.commit()
    finally:
        db.close()


@app.get("/api/meta")
def meta():
    return {"difficulties": DIFFICULTIES,
            "voices": VOICES, "rates": [1.0, 0.85, 0.75, 0.5]}
