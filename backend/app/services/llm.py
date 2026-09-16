import json
import re
import requests
from sqlalchemy import select
from app.config import LLM_MODEL
from app.db.database import SessionLocal
from app.db.models import Setting

# 各厂商 OpenAI 兼容端点预设
PROVIDERS = {
    "zhipu": {"label": "智谱 GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "anthropic_compat": {"label": "Anthropic 兼容网关", "base_url": "https://api.anthropic.com/v1", "model": "claude-3-5-haiku-latest"},
    "custom": {"label": "自定义（OpenAI 兼容）", "base_url": "", "model": ""},
}


def get_llm_config() -> dict:
    """从 settings 表读取 LLM 配置（前端可随时修改）。"""
    db = SessionLocal()
    try:
        rows = {r.key: r.value for r in db.scalars(select(Setting)).all()}
    finally:
        db.close()
    # 注意：用 or 而非默认值，避免数据库里存了空字符串时覆盖掉默认配置
    return {
        "provider": rows.get("llm_provider") or "zhipu",
        "base_url": rows.get("llm_base_url") or PROVIDERS["zhipu"]["base_url"],
        "api_key": rows.get("llm_api_key") or "",
        "model": rows.get("llm_model") or LLM_MODEL,
    }


def set_llm_config(cfg: dict):
    db = SessionLocal()
    try:
        for k in ("llm_provider", "llm_base_url", "llm_api_key", "llm_model"):
            if k not in cfg:
                continue
            row = db.get(Setting, k)
            if row:
                row.value = str(cfg[k])
            else:
                db.add(Setting(key=k, value=str(cfg[k])))
        db.commit()
    finally:
        db.close()


def test_llm_config(cfg: dict) -> tuple[bool, str]:
    """用给定配置发一条最小请求验证连通性。"""
    try:
        resp = requests.post(
            f"{cfg['base_url'].rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            json={"model": cfg["model"],
                  "messages": [{"role": "user", "content": "hi"}],
                  "max_tokens": 5},
            timeout=20)
        if resp.status_code == 200:
            return True, "连接成功"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


def _chat(prompt: str, system: str = "You are an English teaching expert.") -> str:
    cfg = get_llm_config()
    if not cfg["api_key"]:
        raise RuntimeError("LLM API Key 未配置，请在「设置 → 模型服务」中填写")
    resp = requests.post(
        f"{cfg['base_url'].rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {cfg['api_key']}"},
        json={"model": cfg["model"], "temperature": 0.8,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": prompt}]},
        timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"LLM 请求失败 HTTP {resp.status_code}: {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"]


def _extract_json(raw: str):
    m = re.search(r"\[.*\]|\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"LLM 返回无法解析: {raw[:200]}")
    return json.loads(m.group(0))


def generate_sentences(difficulty: str, topic: str, count: int = 1) -> list[dict]:
    from app.config import DIFFICULTIES
    desc = {d["code"]: d["desc"] for d in DIFFICULTIES}
    prompt = (
        f"Generate {count} distinct English sentences for listening practice.\n"
        f"Difficulty ({difficulty}): {desc.get(difficulty, 'natural everyday English')}.\n"
        f"Topic: {topic}.\n"
        "Return ONLY a JSON array like "
        '[{"text":"...","translation":"中文翻译"}]. No other words.')
    return _extract_json(_chat(prompt))


def generate_distractors(text: str, topic: str) -> list[str]:
    prompt = (
        "For the listening-quiz sentence below, create 3 plausible WRONG options.\n"
        "Techniques: near-homophone word swaps, similar sentence patterns, same-topic "
        "confusion. Keep similar length. Each must clearly differ in meaning from the "
        "original. Do NOT use the original sentence.\n"
        f"Topic: {topic}\nSentence: {text}\n"
        'Return ONLY a JSON array of 3 strings.')
    res = _extract_json(_chat(prompt))
    return [str(s) for s in res][:3]
