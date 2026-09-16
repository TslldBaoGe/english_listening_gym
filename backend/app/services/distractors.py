"""本地干扰项生成：LLM 不可用或返回不足时的兜底。

原则：干扰项必须与原文「明显不同但看起来合理」，且彼此不重复。
纯规则实现，零依赖、离线可用，保证测验不会因为选项凑不够而失败。
"""
import re

from app.services.text_utils import normalize, similarity

# 常见可互换词（同类混淆 / 近音）
SWAPS = {
    "coffee": ["tea", "juice", "milk"],
    "tea": ["coffee", "water", "juice"],
    "water": ["juice", "milk", "tea"],
    "juice": ["water", "milk", "coffee"],
    "cup": ["glass", "bottle", "mug"],
    "glass": ["cup", "bottle", "mug"],
    "bottle": ["cup", "glass", "can"],
    "morning": ["evening", "afternoon", "night"],
    "evening": ["morning", "afternoon", "night"],
    "afternoon": ["morning", "evening", "night"],
    "today": ["yesterday", "tomorrow"],
    "yesterday": ["today", "tomorrow"],
    "tomorrow": ["today", "yesterday"],
    "breakfast": ["lunch", "dinner"],
    "lunch": ["breakfast", "dinner"],
    "dinner": ["lunch", "breakfast"],
    "pizza": ["pasta", "sandwich", "soup"],
    "pasta": ["pizza", "rice", "noodles"],
    "movie": ["play", "concert", "documentary"],
    "read": ["wrote", "bought", "borrowed"],
    "bought": ["sold", "borrowed", "lent"],
    "borrowed": ["bought", "lent", "returned"],
    "tired": ["hungry", "excited", "nervous"],
    "happy": ["worried", "tired", "surprised"],
    "expensive": ["cheap", "affordable", "reasonable"],
    "cheap": ["expensive", "costly", "pricey"],
    "increase": ["decrease", "remain stable"],
    "decrease": ["increase", "stay the same"],
    "teacher": ["student", "professor", "tutor"],
    "student": ["teacher", "professor", "researcher"],
    "library": ["laboratory", "bookstore", "cafeteria"],
    "hospital": ["clinic", "pharmacy", "school"],
    "airport": ["station", "harbor", "hotel"],
    "train": ["bus", "plane", "subway"],
    "bus": ["train", "taxi", "subway"],
    "flight": ["train", "bus", "ship"],
    "hotel": ["hostel", "apartment", "airport"],
    "meeting": ["interview", "lecture", "appointment"],
    "interview": ["meeting", "lecture", "seminar"],
    "lecture": ["seminar", "meeting", "workshop"],
    "report": ["essay", "proposal", "summary"],
    "essay": ["report", "proposal", "thesis"],
    "computer": ["laptop", "tablet", "phone"],
    "laptop": ["desktop", "tablet", "phone"],
    "phone": ["tablet", "laptop", "camera"],
    "weather": ["traffic", "schedule", "budget"],
    "price": ["quality", "quantity", "size"],
    "begin": ["finish", "delay", "cancel"],
    "finish": ["begin", "postpone", "cancel"],
    "arrive": ["leave", "depart", "return"],
    "leave": ["arrive", "stay", "return"],
    "buy": ["sell", "rent", "borrow"],
    "sell": ["buy", "rent", "donate"],
    "difficult": ["simple", "boring", "useful"],
    "simple": ["difficult", "complex", "confusing"],
    "important": ["optional", "minor", "unusual"],
    "always": ["never", "rarely", "sometimes"],
    "never": ["always", "often", "sometimes"],
    "often": ["rarely", "never", "occasionally"],
    "usually": ["rarely", "never", "occasionally"],
}

NUMBERS = {
    "one": ["two", "three"], "two": ["three", "four"], "three": ["four", "five"],
    "four": ["five", "six"], "five": ["six", "seven"],
    "first": ["second", "third"], "second": ["third", "fourth"],
    "third": ["fourth", "fifth"],
    "half": ["quarter", "third"], "double": ["triple", "half"],
}

TIME_BUCKETS = [
    ["every morning", "every afternoon", "every evening", "every night"],
    ["every day", "every week", "every weekend", "every month"],
    ["on Monday", "on Tuesday", "on Friday", "on Sunday"],
    ["last week", "last month", "last year", "yesterday"],
    ["next week", "next month", "next year", "tomorrow"],
    ["in the morning", "in the afternoon", "in the evening", "at night"],
]

# 通用内容词池，仅在词表替换全部落空时兜底使用
GENERIC_WORDS = [
    "energy", "matter", "material", "process", "method", "result", "reason",
    "problem", "system", "project", "report", "record", "period", "factor",
    "effect", "issue", "amount", "value", "service", "object", "detail",
]

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "so", "that", "this", "these", "those",
    "of", "to", "in", "on", "at", "for", "with", "from", "into", "by", "about",
    "is", "are", "was", "were", "be", "been", "being", "am", "do", "does", "did",
    "have", "has", "had", "will", "would", "can", "could", "should", "must",
    "may", "might", "not", "than", "then", "when", "while", "after", "before",
    "his", "her", "its", "their", "our", "your", "my", "he", "she", "it", "they",
    "we", "you", "i", "as", "if", "because", "there", "here", "very", "more",
    "most", "some", "any", "all", "each", "both", "other", "such", "only",
}

_WORD = re.compile(r"[A-Za-z']+")
_AUX = re.compile(r"\b(am|is|are|was|were|do|does|did|can|could|will|would|"
                  r"should|must|may|might|have|has|had)\b", re.I)


def _swap_word(word: str, replacement: str) -> str:
    """保留原词的大小写形态。"""
    m = _WORD.search(word)
    if not m:
        return word
    core = m.group(0)
    if core.isupper():
        new = replacement.upper()
    elif core[0].isupper():
        new = replacement.capitalize()
    else:
        new = replacement
    return word[:m.start()] + new + word[m.end():]


def _variants(text: str) -> list[str]:
    """由原句派生候选干扰项。"""
    out = []
    words = text.split()

    for i, w in enumerate(words):
        core = _WORD.search(w)
        if not core:
            continue
        core = core.group(0).lower()
        for rep in list(SWAPS.get(core, [])) + list(NUMBERS.get(core, [])):
            out.append(" ".join(words[:i] + [_swap_word(w, rep)] + words[i + 1:]))

    # 时间短语只在同一类内互换，避免出现 "until every morning" 这种病句
    low = text.lower()
    for bucket in TIME_BUCKETS:
        for phrase in bucket:
            if phrase in low:
                for other in bucket:
                    if other != phrase:
                        out.append(re.sub(re.escape(phrase), other, text, flags=re.I))

    # 兜底一：否定句，语义明显不同且语法成立
    if _AUX.search(text):
        out.append(_AUX.sub(lambda m: m.group(0) + " not", text, count=1))

    # 兜底二：通用内容词替换（仅保证选项可用，语义合理度有限）
    # 先替换「名词位」（前面是冠词/介词的词），再从后往前替换其他内容词
    dets = {"the", "a", "an", "of", "into", "for", "with", "on", "in", "to", "from"}
    ordered = []
    for i, w in enumerate(words):
        core = _WORD.search(w)
        if not core or i == 0:
            continue
        c = core.group(0).lower()
        if c in STOPWORDS or c in SWAPS or c in NUMBERS or len(c) < 4:
            continue
        prev = _WORD.search(words[i - 1])
        nounish = bool(prev) and prev.group(0).lower() in dets
        ordered.append((0 if nounish else 1, -i, i, c))
    ordered.sort()

    for _, _, i, c in ordered:
        near = sorted(GENERIC_WORDS, key=lambda g: abs(len(g) - len(c)))[:2]
        for rep in near:
            if rep != c:
                out.append(" ".join(words[:i] + [_swap_word(words[i], rep)] + words[i + 1:]))

    return out


def make_distractors(text: str, pool=(), k: int = 3) -> list[str]:
    """生成至多 k 个干扰项；pool 为优先使用的库内其他句子。"""
    target = normalize(text)
    chosen: list[str] = []
    for cand in list(pool) + _variants(text):
        cand = (cand or "").strip()
        if not cand or normalize(cand) == target:
            continue
        if similarity(cand, text) >= 0.97:      # 与原句过于接近
            continue
        if any(similarity(cand, c) >= 0.95 for c in chosen):  # 干扰项彼此太像
            continue
        chosen.append(cand)
        if len(chosen) >= k:
            break
    return chosen
