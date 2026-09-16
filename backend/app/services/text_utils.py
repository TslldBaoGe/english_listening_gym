"""文本归一化与相似度工具，供去重和干扰项生成共用。"""
import re
from difflib import SequenceMatcher

_PUNCT = re.compile(r"[^a-z0-9\s']")


def normalize(text: str) -> str:
    """小写、去标点、压缩空白，用于词面比较。"""
    t = _PUNCT.sub(" ", (text or "").lower())
    return re.sub(r"\s+", " ", t).strip()


def similarity(a: str, b: str) -> float:
    """归一化后的词面相似度，0~1。"""
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()
