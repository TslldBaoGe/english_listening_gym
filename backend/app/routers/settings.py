import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Setting, Sentence
from app.services import llm

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULTS = {"difficulty": "L1", "topic": "daily life", "voice": "aria", "rate": "1.0"}

TOPICS_KEY = "topics"           # 主题候选列表（JSON 数组），设置页下拉框用
DEFAULT_TOPICS = ["daily life", "travel", "campus", "work", "food",
                  "shopping", "health", "tech"]


def _rows(db: Session) -> dict:
    return {r.key: r.value for r in db.scalars(select(Setting)).all()}


def _topics(db: Session) -> list[str]:
    """读主题列表；还没设置过就给出默认几个 + 知识库里已经用过的主题。"""
    raw = _rows(db).get(TOPICS_KEY)
    if raw:
        try:
            saved = [str(t).strip() for t in json.loads(raw)]
            saved = [t for t in saved if t]
            if saved:
                return saved
        except Exception:
            pass
    used = {str(t).strip() for t in db.scalars(select(Sentence.topic).distinct()).all()
            if t and str(t).strip()}
    out: list[str] = []
    for t in DEFAULT_TOPICS + sorted(used):
        if t not in out:
            out.append(t)
    return out


def _all_settings(db: Session) -> dict:
    rows = _rows(db)
    out = {**DEFAULTS, **rows}
    out["rate"] = float(out.get("rate") or 1.0)
    out["topics"] = _topics(db)
    return out


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    out = _all_settings(db)
    if out.get("llm_api_key"):
        out["llm_api_key"] = llm.mask_key(out["llm_api_key"])  # 脱敏返回
    return out


@router.put("")
def put_settings(body: dict, db: Session = Depends(get_db)):
    llm_fields = {"llm_provider", "llm_base_url", "llm_api_key", "llm_model"}
    for k, v in body.items():
        if k in llm_fields:
            if k == "llm_api_key" and (not v or str(v).endswith("***")):
                continue  # 脱敏值不覆盖真实 key
            llm.set_llm_config({k: v})
        elif k == TOPICS_KEY:
            items = [str(t).strip() for t in (v or []) if str(t).strip()]
            row = db.get(Setting, k)
            value = json.dumps(items, ensure_ascii=False)
            if row:
                row.value = value
            else:
                db.add(Setting(key=k, value=value))
        elif k in DEFAULTS:
            row = db.get(Setting, k)
            if row:
                row.value = str(v)
            else:
                db.add(Setting(key=k, value=str(v)))
    db.commit()
    return get_settings(db)


@router.get("/llm/providers")
def llm_providers():
    return llm.PROVIDERS


@router.get("/llm/configs")
def llm_configs():
    """模型配置列表（可命名、可删除，密钥脱敏返回）。"""
    return llm.list_llm_configs()


@router.post("/llm/configs")
def llm_config_save(body: dict):
    """新增或修改一条模型配置（body 带 id 即修改）。"""
    return llm.save_llm_config(body)


@router.delete("/llm/configs/{cid}")
def llm_config_delete(cid: str):
    return llm.delete_llm_config(cid)


@router.post("/llm/configs/{cid}/activate")
def llm_config_activate(cid: str):
    """把某条配置设为当前使用。"""
    return llm.activate_llm_config(cid)


def _merged_llm_cfg(body: dict) -> dict:
    """合并前端提交值与已保存配置：脱敏/空值回退到数据库保存的真实值。"""
    cid = str(body.get("id") or "").strip()
    saved = llm.get_config_by_id(cid) if cid else llm.get_llm_config()
    api_key = body.get("api_key") or ""
    if not api_key or api_key.endswith("***"):
        api_key = saved["api_key"]
    return {
        "base_url": (body.get("base_url") or saved["base_url"]).rstrip("/"),
        "api_key": api_key,
        "model": body.get("model") or saved["model"],
    }


@router.post("/llm/test")
def llm_test(body: dict):
    cfg = _merged_llm_cfg(body)
    if not cfg["api_key"]:
        return {"ok": False, "msg": "请先填写有效的 API Key"}
    if not cfg["base_url"]:
        return {"ok": False, "msg": "请先填写 BASE URL"}
    ok, msg = llm.test_llm_config(cfg)
    return {"ok": ok, "msg": msg}


@router.post("/llm/models")
def llm_models(body: dict):
    """从 {base_url}/models 拉取可用模型列表（OpenAI 兼容协议）。"""
    cfg = _merged_llm_cfg(body)
    ok, msg, models = llm.list_models(cfg)
    return {"ok": ok, "msg": msg, "models": models}
