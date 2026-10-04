import json
import re
import uuid
import requests
from sqlalchemy import select
from app.config import LLM_MODEL
from app.db.database import SessionLocal
from app.db.models import Setting

# 模型类型：只保留「自定义（OpenAI 兼容）」，地址/密钥/模型名等全部由用户自行填写
PROVIDERS = {
    "custom": {"label": "自定义（OpenAI 兼容）", "base_url": "", "model": ""},
}

CONFIGS_KEY = "llm_configs"    # 模型配置列表（JSON 数组）
ACTIVE_KEY = "llm_active_id"   # 当前启用哪一条


def mask_key(key: str) -> str:
    return (key[:6] + "***") if key else ""


def _norm(item: dict) -> dict:
    return {
        "id": str(item.get("id") or uuid.uuid4().hex[:8]),
        "name": str(item.get("name") or "未命名配置"),
        "base_url": str(item.get("base_url") or "").rstrip("/"),
        "api_key": str(item.get("api_key") or ""),
        "model": str(item.get("model") or ""),
    }


def _rows(db) -> dict:
    return {r.key: r.value for r in db.scalars(select(Setting)).all()}


def _put(db, key: str, value):
    row = db.get(Setting, key)
    if row:
        row.value = "" if value is None else str(value)
    else:
        db.add(Setting(key=key, value="" if value is None else str(value)))


def _load_configs(db) -> list[dict]:
    """读取配置列表；老版本的单条配置在首次访问时自动迁移成一条命名配置。"""
    rows = _rows(db)
    raw = rows.get(CONFIGS_KEY)
    if raw:
        try:
            items = [i for i in json.loads(raw) if isinstance(i, dict)]
            return [_norm(i) for i in items]
        except Exception:
            pass
    legacy = {"base_url": rows.get("llm_base_url") or "",
              "api_key": rows.get("llm_api_key") or "",
              "model": rows.get("llm_model") or ""}
    if any(legacy.values()):
        item = _norm({"name": "默认配置", **legacy})
        _save_configs(db, [item], item["id"])
        db.commit()
        return [item]
    return []


def _sync_active(db, items: list[dict], active_id: str):
    """把「当前启用」那条同步进旧的 llm_* 键，练习/测验的 LLM 调用继续直接读这些键。"""
    cur = next((i for i in items if i["id"] == active_id), None) or (items[0] if items else None)
    _put(db, "llm_provider", "custom")
    _put(db, "llm_base_url", cur["base_url"] if cur else "")
    _put(db, "llm_api_key", cur["api_key"] if cur else "")
    _put(db, "llm_model", cur["model"] if cur else "")


def _save_configs(db, items: list[dict], active_id: str):
    _put(db, CONFIGS_KEY, json.dumps(items, ensure_ascii=False))
    _put(db, ACTIVE_KEY, active_id or "")
    _sync_active(db, items, active_id)


def _payload(items: list[dict], active_id: str, focus_id: str = "") -> dict:
    """返回给前端：密钥脱敏，只带前 6 位 + ***，保存时原样回传即可保留旧密钥。"""
    return {
        "items": [{"id": i["id"], "name": i["name"], "base_url": i["base_url"],
                   "api_key": mask_key(i["api_key"]), "has_key": bool(i["api_key"]),
                   "model": i["model"], "active": i["id"] == active_id} for i in items],
        "active_id": active_id,
        "focus_id": focus_id,
        "total": len(items),
    }


def get_llm_config() -> dict:
    """读取当前启用的 LLM 配置（由 _sync_active 维护，练习/测验生成时使用）。"""
    db = SessionLocal()
    try:
        rows = _rows(db)
    finally:
        db.close()
    # 注意：用 or 而非默认值，避免数据库里存了空字符串时覆盖掉默认配置
    return {
        "provider": rows.get("llm_provider") or "custom",
        "base_url": rows.get("llm_base_url") or "",
        "api_key": rows.get("llm_api_key") or "",
        "model": rows.get("llm_model") or LLM_MODEL,
    }


def get_config_by_id(cid: str) -> dict:
    db = SessionLocal()
    try:
        for i in _load_configs(db):
            if i["id"] == cid:
                return i
    finally:
        db.close()
    return get_llm_config()


def list_llm_configs() -> dict:
    db = SessionLocal()
    try:
        items = _load_configs(db)
        active = _rows(db).get(ACTIVE_KEY) or (items[0]["id"] if items else "")
        if items and _rows(db).get(ACTIVE_KEY) != active:
            _save_configs(db, items, active)
            db.commit()
        return _payload(items, active)
    finally:
        db.close()


def save_llm_config(cfg: dict) -> dict:
    """新增或修改一条配置；cfg 带 id 就是修改。密钥为脱敏值/空值时保留原来保存的。"""
    db = SessionLocal()
    try:
        items = _load_configs(db)
        cid = str(cfg.get("id") or "").strip()
        cur = next((i for i in items if i["id"] == cid), None)
        key = str(cfg.get("api_key") or "")
        if cur is not None and (not key or key.endswith("***")):
            key = cur["api_key"]
        data = {"name": str(cfg.get("name") or "").strip() or "未命名配置",
                "base_url": str(cfg.get("base_url") or "").strip().rstrip("/"),
                "api_key": key,
                "model": str(cfg.get("model") or "").strip()}
        if cur is None:
            cur = _norm(data)
            items.append(cur)
        else:
            cur.update(data)
        active = _rows(db).get(ACTIVE_KEY) or ""
        if cfg.get("make_active", True) or not active:
            active = cur["id"]
        _save_configs(db, items, active)
        db.commit()
        return _payload(items, active, focus_id=cur["id"])
    finally:
        db.close()


def delete_llm_config(cid: str) -> dict:
    db = SessionLocal()
    try:
        items = [i for i in _load_configs(db) if i["id"] != cid]
        ids = [i["id"] for i in items]
        active = _rows(db).get(ACTIVE_KEY) or ""
        if active not in ids:
            active = ids[0] if ids else ""
        _save_configs(db, items, active)
        db.commit()
        return _payload(items, active)
    finally:
        db.close()


def activate_llm_config(cid: str) -> dict:
    db = SessionLocal()
    try:
        items = _load_configs(db)
        ids = [i["id"] for i in items]
        active = cid if cid in ids else (ids[0] if ids else "")
        _save_configs(db, items, active)
        db.commit()
        return _payload(items, active)
    finally:
        db.close()


def set_llm_config(cfg: dict):
    """旧接口写入：写 llm_* 键的同时同步到列表里当前启用那条，避免两处不一致。"""
    db = SessionLocal()
    try:
        for k in ("llm_provider", "llm_base_url", "llm_api_key", "llm_model"):
            if k in cfg:
                _put(db, k, cfg[k])
        db.commit()
        rows = _rows(db)
        items = _load_configs(db)
        active = rows.get(ACTIVE_KEY) or (items[0]["id"] if items else "")
        cur = next((i for i in items if i["id"] == active), None)
        if cur is not None:
            for key, field in (("llm_base_url", "base_url"), ("llm_api_key", "api_key"),
                               ("llm_model", "model")):
                if key in cfg:
                    cur[field] = str(cfg[key])
            _save_configs(db, items, active)
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
