import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
CHROMA_DIR = DATA_DIR / "chroma"
DB_PATH = DATA_DIR / "app.db"

for d in (DATA_DIR, AUDIO_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash")

DEFAULT_VOICE = "en-US-AriaNeural"
VOICES = {"aria": "en-US-AriaNeural", "guy": "en-US-GuyNeural"}

# 前端语速 -> edge-tts rate 百分比
RATE_MAP = {1.0: "+0%", 0.85: "-15%", 0.75: "-25%", 0.5: "-50%"}

DIFFICULTIES = [
    {"code": "L1", "ielts": "5.0", "cefr": "B1",
     "label": "入门",
     "desc": "simple sentences, core vocabulary (top 1500 words), everyday topics, no idioms"},
    {"code": "L2", "ielts": "5.5-6.0", "cefr": "B1+",
     "label": "基础",
     "desc": "common compound sentences, daily-life topics, natural collocations"},
    {"code": "L3", "ielts": "6.5", "cefr": "B2",
     "label": "进阶",
     "desc": "nested clauses, academic and life scenarios, common phrasal verbs and collocations"},
    {"code": "L4", "ielts": "7.0", "cefr": "C1",
     "label": "高阶",
     "desc": "long complex sentences, lecture style, idioms, reduced forms in speech"},
    {"code": "L5", "ielts": "7.5+", "cefr": "C2",
     "label": "挑战",
     "desc": "fast natural speech style, complex structures, professional and abstract topics, slang"},
]

# 去重：满足任一条件即视为重复
# Chroma 默认 l2 空间给出的距离是「平方 L2」，等于 2-2cos
# 实测：几乎同义句 0.11~0.30，不同主题 1.6~1.8，故取 0.35 可稳定拦住近似句
DUP_DISTANCE = 0.35
# 词面相似度（归一化后的 SequenceMatcher 比值），兜底拦截换词模板句
DUP_TEXT_SIM = 0.85
QUIZ_SESSION_TTL = 3600  # 秒
