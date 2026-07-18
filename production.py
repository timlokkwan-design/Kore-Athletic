"""Production mode — skip sample data and dev-only UI."""
from __future__ import annotations

import os
from pathlib import Path

PRODUCTION_FLAG = Path(__file__).resolve().parent.parent / "data" / ".production"


def _secrets_production_enabled() -> bool:
    try:
        import streamlit as st

        for block in (st.secrets.get("production", {}), st.secrets.get("app", {})):
            val = block.get("enabled", block.get("production"))
            if val is True or str(val).strip().lower() in {"1", "true", "yes", "on"}:
                return True
    except Exception:
        pass
    return False


def is_production() -> bool:
    env = os.environ.get("KORE_PRODUCTION", "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    if _secrets_production_enabled():
        return True
    if PRODUCTION_FLAG.exists():
        return True
    # Streamlit Cloud + Supabase = 正式部署，不注入測試資料
    try:
        from utils.cloud_deploy import is_streamlit_cloud
        from utils.supabase_config import is_supabase_enabled

        if is_streamlit_cloud() and is_supabase_enabled():
            return True
    except Exception:
        pass
    return False


def enable_production_mode() -> None:
    PRODUCTION_FLAG.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTION_FLAG.write_text("production\n", encoding="utf-8")
