"""听写/跟读判定：把用户输入的句子和原文做词级比对。

比对前先做归一化（小写、去标点、压缩空白），所以大小写、标点、多余空格都
不算错；除此之外要求逐词一致。返回可直接给前端渲染的片段，方便把写错/漏掉
的词标出来。
"""
from difflib import SequenceMatcher

from app.services.text_utils import normalize


def _tokens(s: str) -> list[str]:
    return normalize(s).split()


def check(expected: str, got: str) -> dict:
    exp, usr = _tokens(expected), _tokens(got)
    correct = exp == usr
    sim = SequenceMatcher(None, exp, usr).ratio() if (exp or usr) else 0.0

    segments: list[dict] = []
    missing: list[str] = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, exp, usr).get_opcodes():
        if tag == "equal":
            segments += [{"v": w, "status": "ok"} for w in usr[j1:j2]]
        elif tag == "replace":
            want, wrote = exp[i1:i2], usr[j1:j2]
            for k, w in enumerate(wrote):
                segments.append({"v": w, "status": "bad",
                                 "want": want[k] if k < len(want) else ""})
            missing += want[len(wrote):]      # 原文里没被写出来的部分算漏掉
        elif tag == "delete":
            missing += exp[i1:i2]
        elif tag == "insert":
            segments += [{"v": w, "status": "bad", "want": ""} for w in usr[j1:j2]]

    return {
        "correct": correct,
        "similarity": round(sim, 3),
        "expected": expected.strip(),
        "segments": segments,
        "missing": missing,
        "extra": [s["v"] for s in segments if s["status"] == "bad" and not s["want"]],
    }
