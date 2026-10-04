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


def _direct_session() -> requests.Session:
    """忽略系统代理/环境变量代理的会话，用于强制直连。"""
    s = requests.Session()
    s.trust_env = False
    return s


def _blocked_by_proxy(resp) -> bool:
    """判断响应是不是本机代理网关返回的 HTML 拦截页。

    典型是 Squid 的「ERROR: ACCESS DENIED ... web cache」页面，
    走代理时才会出现，直连同一个地址是正常的。
    """
    return (resp.status_code in (403, 407)
            and "html" in (resp.headers.get("content-type") or "").lower())


def _post(url: str, headers: dict, payload: dict, timeout: int, no_proxy: bool = False):
    """POST 请求；no_proxy 时强制直连，否则被代理拦截时自动直连重试一次。"""
    if no_proxy:
        with _direct_session() as s:
            return s.post(url, headers=headers, json=payload, timeout=timeout)
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if _blocked_by_proxy(resp):
        with _direct_session() as s:
            retry = s.post(url, headers=headers, json=payload, timeout=timeout)
        if retry.status_code == 200:
            return retry
    return resp


def _get(url: str, headers: dict, timeout: int, no_proxy: bool = False):
    """GET 请求；同 _post，代理拦截时自动直连重试。"""
    if no_proxy:
        with _direct_session() as s:
            return s.get(url, headers=headers, timeout=timeout)
    resp = requests.get(url, headers=headers, timeout=timeout)
    if _blocked_by_proxy(resp):
        with _direct_session() as s:
            retry = s.get(url, headers=headers, timeout=timeout)
        if retry.status_code == 200:
            return retry
    return resp


def _norm(item: dict) -> dict:
    return {
        "id": str(item.get("id") or uuid.uuid4().hex[:8]),
        "name": str(item.get("name") or "未命名配置"),
        "base_url": str(item.get("base_url") or "").rstrip("/"),
        "api_key": str(item.get("api_key") or ""),
        "model": str(item.get("model") or ""),
        "no_proxy": bool(item.get("no_proxy")),
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
                   "model": i["model"], "no_proxy": i["no_proxy"],
                   "active": i["id"] == active_id} for i in items],
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
                "model": str(cfg.get("model") or "").strip(),
                "no_proxy": bool(cfg.get("no_proxy"))}
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
        resp = _post(
            f"{cfg['base_url'].rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            payload={"model": cfg["model"],
                     "messages": [{"role": "user", "content": "hi"}],
                     "max_tokens": 5},
            timeout=20,
            no_proxy=bool(cfg.get("no_proxy")))
        if resp.status_code == 200:
            return True, "连接成功"
        if _blocked_by_proxy(resp):
            return False, (f"HTTP {resp.status_code}: {resp.text[:160]}\n"
                           "这是本机代理网关的拦截页（直连重试也没通）。"
                           "请在代理软件里把该域名设为直连，或勾选「不使用系统代理」。")
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


def list_models(cfg: dict) -> tuple[bool, str, list[str]]:
    """从 {base_url}/models 拉取可用模型列表（OpenAI 兼容协议）。"""
    base_url = (cfg.get("base_url") or "").rstrip("/")
    api_key = cfg.get("api_key") or ""
    if not base_url:
        return False, "请先填写 BASE URL", []
    if not api_key:
        return False, "请先填写有效的 API Key", []
    try:
        resp = _get(f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=20, no_proxy=bool(cfg.get("no_proxy")))
        if resp.status_code != 200:
            msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
            if _blocked_by_proxy(resp):
                msg = (f"HTTP {resp.status_code}: {resp.text[:160]}\n"
                       "这是本机代理网关的拦截页（直连重试也没通）。"
                       "请在代理软件里把该域名设为直连，或勾选「不使用系统代理」。")
            return False, msg, []
        data = resp.json().get("data", [])
        models = sorted(str(m.get("id", "")) for m in data if m.get("id"))
        return True, f"获取到 {len(models)} 个模型", models
    except Exception as e:
        return False, str(e), []


def _chat(prompt: str, system: str = "You are an English teaching expert.") -> str:
    cfg = get_llm_config()
    if not cfg["api_key"]:
        raise RuntimeError("LLM API Key 未配置，请在「设置 → 模型服务」中填写")
    resp = _post(
        f"{cfg['base_url'].rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {cfg['api_key']}"},
        payload={"model": cfg["model"], "temperature": 0.8,
                 "messages": [{"role": "system", "content": system},
                              {"role": "user", "content": prompt}]},
        timeout=60,
        no_proxy=bool(cfg.get("no_proxy")))
    if resp.status_code != 200:
        raise RuntimeError(f"LLM 请求失败 HTTP {resp.status_code}: {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"]


def _extract_json(raw: str):
    m = re.search(r"\[.*\]|\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"LLM 返回无法解析: {raw[:200]}")
    return json.loads(m.group(0))


VARIATION_ANGLES = [
    "Focus on a different everyday scenario (work / shopping / transport / study).",
    "Change the subject and the scene completely.",
    "Use a different verb tense (past / future / present perfect).",
    "Add one concrete, memorable detail instead of a generic statement.",
    "Shift to a different place or time of day.",
]


def generate_sentences(difficulty: str, topic: str, count: int = 1,
                       avoid: list[str] | None = None, attempt: int = 0) -> list[dict]:
    from app.config import DIFFICULTIES
    desc = {d["code"]: d["desc"] for d in DIFFICULTIES}
    prompt = (
        f"Generate {count} distinct English sentences for listening practice.\n"
        f"Difficulty ({difficulty}): {desc.get(difficulty, 'natural everyday English')}.\n"
        f"Topic: {topic}.\n")
    if avoid:
        listed = "\n".join(f"- {t}" for t in avoid[:12])
        prompt += (
            "The learner ALREADY has the sentences below. Do NOT repeat them and do NOT "
            "just swap one word; use clearly different scenarios, subjects or tenses:\n"
            f"{listed}\n")
    if attempt:
        prompt += f"Variation hint: {VARIATION_ANGLES[attempt % len(VARIATION_ANGLES)]}\n"
    prompt += ("Return ONLY a JSON array like "
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
