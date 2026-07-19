"""In-memory cache for Supabase/CSV reads within a Streamlit session."""
from __future__ import annotations

from typing import Callable, TypeVar

import pandas as pd

T = TypeVar("T")

_CACHE_KEY = "_ka_data_cache"
_VERSION_KEY = "_ka_data_version"


def _in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


def _cache_bucket() -> dict:
    import streamlit as st

    if _CACHE_KEY not in st.session_state:
        st.session_state[_CACHE_KEY] = {}
    return st.session_state[_CACHE_KEY]


def _cache_version() -> int:
    import streamlit as st

    return int(st.session_state.get(_VERSION_KEY, 0))


def invalidate_data_cache() -> None:
    """Call after writes so the next read hits Supabase/CSV again."""
    if not _in_streamlit():
        return
    import streamlit as st

    st.session_state[_VERSION_KEY] = _cache_version() + 1
    st.session_state[_CACHE_KEY] = {}


def drop_cache_keys(*keys: str) -> None:
    """Drop specific cache entries without bumping the global version."""
    if not _in_streamlit() or not keys:
        return
    bucket = _cache_bucket()
    for key in keys:
        bucket.pop(key, None)


def cached_dataframe(key: str, loader: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    if not _in_streamlit():
        return loader()
    ver = _cache_version()
    bucket = _cache_bucket()
    entry = bucket.get(key)
    if entry and entry[0] == ver:
        return entry[1].copy()
    df = loader()
    bucket[key] = (ver, df.copy())
    return df.copy()


def cached_value(key: str, loader: Callable[[], T]) -> T:
    if not _in_streamlit():
        return loader()
    ver = _cache_version()
    bucket = _cache_bucket()
    entry = bucket.get(key)
    if entry and entry[0] == ver:
        return entry[1]
    value = loader()
    bucket[key] = (ver, value)
    return value
