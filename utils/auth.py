"""Simple CSV-based authentication."""

from __future__ import annotations

import streamlit as st

from utils.data_store import get_user, set_user_password
from utils.helpers import safe_str
from utils.passwords import is_hashed, verify_password
from utils.permissions import PermissionDenied, check_role, require_login
from utils.nav_persist import clear_nav_state
from utils.session_persist import clear_persisted_login, persist_login


def _public_user(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != "password"}


def get_current_user() -> dict | None:
    return st.session_state.get("user")


def refresh_current_user() -> dict | None:
    user = get_current_user()
    if not user:
        return None
    fresh = get_user(safe_str(user.get("username")))
    if fresh:
        st.session_state.user = _public_user(fresh)
        return st.session_state.user
    return user


def get_current_role() -> str:
    user = get_current_user()
    return user["role"] if user else "visitor"


def _home_page_for_role(role: str) -> str:
    return {"coach": "教練平台", "student": "學生平台", "parent": "家長專區"}.get(role, "PB 排行榜")


def login(username: str, password: str) -> tuple[bool, str]:
    name = username.strip()
    user = get_user(name)
    if not user:
        return False, "帳號或密碼錯誤"
    stored = str(user.get("password", ""))
    if not verify_password(password, stored):
        return False, "帳號或密碼錯誤"
    if user.get("role") == "pending":
        return False, "帳號待教練審批中"
    if user.get("role") == "removed":
        return False, "此帳號已移出隊伍，請聯絡教練"
    if not is_hashed(stored):
        set_user_password(name, password)
        user = get_user(name) or user
    st.session_state.user = _public_user(user)
    role = safe_str(user.get("role"))
    st.session_state.main_page = _home_page_for_role(role)
    st.session_state._fresh_login = True
    for key in ("_nav_restored", "_nav_bridge_injected", "_cookie_restore_done", "_storage_bridge_done"):
        st.session_state.pop(key, None)
    persist_login(name)
    from utils.nav_persist import save_nav_state

    save_nav_state(role, main_page=st.session_state.main_page)
    return True, ""


def logout() -> None:
    import time

    # Block cookie/localStorage auto-restore for a short window (fast, no race).
    st.session_state["_logout_at"] = time.time()
    st.session_state.pop("user", None)
    clear_persisted_login()
    clear_nav_state()
    st.session_state.pop("_nav_restored", None)
    st.session_state.pop("_nav_bridge_injected", None)
    st.session_state.pop("_fresh_login", None)


def require_roles(*roles: str) -> bool:
    """Return True if current user has one of the allowed roles."""
    try:
        check_role(*roles)
        return True
    except PermissionDenied:
        return False


def require_roles_or_stop(*roles: str) -> dict:
    try:
        return check_role(*roles)
    except PermissionDenied as exc:
        st.error(exc.message)
        st.stop()


def require_coach_or_stop() -> dict:
    return require_roles_or_stop("coach")


def require_student_or_stop() -> dict:
    return require_roles_or_stop("student")


def require_parent_or_stop() -> dict:
    return require_roles_or_stop("parent")


def require_login_or_stop() -> dict:
    try:
        return require_login()
    except PermissionDenied as exc:
        st.error(exc.message)
        st.stop()
