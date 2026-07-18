"""Persist login across browser refresh via signed HTTP cookie."""

from __future__ import annotations

import hashlib
import hmac
import time

import streamlit as st

COOKIE_NAME = "ka_auth"
MAX_AGE_DAYS = 30


def _cookie_secret() -> str:
    try:
        secret = st.secrets.get("auth", {}).get("cookie_secret", "")
        if secret:
            return str(secret)
    except Exception:
        pass
    return "kore-athletic-dev-cookie-secret-change-me"


def _sign(username: str, exp: int) -> str:
    secret = _cookie_secret()
    msg = f"{username}|{exp}"
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"{username}|{exp}|{sig}"


def _verify(token: str) -> str | None:
    parts = str(token).split("|")
    if len(parts) != 3:
        return None
    username, exp_s, sig = parts
    try:
        exp = int(exp_s)
    except ValueError:
        return None
    if exp < int(time.time()):
        return None
    secret = _cookie_secret()
    msg = f"{username}|{exp}"
    expected = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return username.strip()


@st.cache_resource
def _cookie_manager():
    import extra_streamlit_components as stx

    return stx.CookieManager(key="ka_auth_cookie_manager")


def persist_login(username: str) -> None:
    from datetime import datetime, timedelta

    exp = int(time.time()) + MAX_AGE_DAYS * 86400
    token = _sign(username.strip(), exp)
    _cookie_manager().set(
        COOKIE_NAME,
        token,
        expires_at=datetime.now() + timedelta(days=MAX_AGE_DAYS),
        key="ka_set_auth_cookie",
    )


def clear_persisted_login() -> None:
    _cookie_manager().delete(COOKIE_NAME, key="ka_del_auth_cookie")
    for key in ("_cookie_restore_done", "_cookie_restore_attempted"):
        st.session_state.pop(key, None)


def try_restore_session() -> None:
    """Restore st.session_state.user from signed cookie if missing."""
    if st.session_state.get("user"):
        return
    if st.session_state.get("_cookie_restore_done"):
        return

    cookies = _cookie_manager().get_all()
    if cookies is None:
        if not st.session_state.get("_cookie_restore_attempted"):
            st.session_state._cookie_restore_attempted = True
            st.rerun()
        return

    st.session_state._cookie_restore_done = True
    token = cookies.get(COOKIE_NAME)
    if not token:
        return

    username = _verify(str(token))
    if not username:
        _cookie_manager().delete(COOKIE_NAME, key="ka_del_bad_cookie")
        return

    from utils.auth import _public_user
    from utils.data_store import get_user

    user = get_user(username)
    if not user:
        return
    if user.get("role") in ("pending", "removed"):
        return
    st.session_state.user = _public_user(user)
