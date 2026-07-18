"""Supabase connection settings — from env, Streamlit secrets, or secrets.toml."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SECRETS_FILE = _PROJECT_ROOT / ".streamlit" / "secrets.toml"


def _load_secrets_toml() -> dict:
    if not _SECRETS_FILE.exists():
        return {}
    try:
        import tomllib

        return tomllib.loads(_SECRETS_FILE.read_bytes())
    except Exception:
        return {}


def get_supabase_credentials() -> tuple[str | None, str | None]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if url and key:
        return url.strip(), key.strip()

    try:
        import streamlit as st

        block = st.secrets.get("supabase", {})
        url = str(block.get("url") or "").strip() or None
        key = str(block.get("service_key") or block.get("key") or "").strip() or None
        if url and key:
            return url, key
    except Exception:
        pass

    block = _load_secrets_toml().get("supabase", {})
    url = str(block.get("url") or "").strip() or None
    key = str(block.get("service_key") or block.get("key") or "").strip() or None
    return url, key


def is_supabase_enabled() -> bool:
    url, key = get_supabase_credentials()
    return bool(url and key)


@lru_cache(maxsize=1)
def get_supabase_client():
    from supabase import create_client

    url, key = get_supabase_credentials()
    if not url or not key:
        raise RuntimeError("Supabase 未設定：請在 Secrets 加入 supabase.url 及 supabase.service_key")
    return create_client(url, key)
