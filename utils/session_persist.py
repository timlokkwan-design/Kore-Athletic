"""Persist login across browser refresh via signed HTTP cookie (no extra deps)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import unquote

import streamlit as st
import streamlit.components.v1 as components

COOKIE_NAME = "ka_auth"
MAX_AGE_SECONDS = 30 * 24 * 60 * 60


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


def _parse_cookie_header(header: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in header.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _read_request_cookies() -> dict[str, str]:
    """Read browser cookies sent with the current Streamlit request."""
    try:
        ctx = st.context
        if hasattr(ctx, "cookies") and ctx.cookies:
            return {str(k): str(v) for k, v in ctx.cookies.items()}
    except Exception:
        pass
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers

        headers = _get_websocket_headers() or {}
        raw = headers.get("Cookie") or headers.get("cookie") or ""
        if raw:
            return _parse_cookie_header(raw)
    except Exception:
        pass
    return {}


def _set_auth_cookie(token: str) -> None:
    components.html(
        f"""
        <script>
        document.cookie = {json.dumps(COOKIE_NAME)} + "=" + encodeURIComponent({json.dumps(token)})
            + "; path=/; max-age={MAX_AGE_SECONDS}; SameSite=Lax";
        </script>
        """,
        height=0,
        width=0,
    )


def _clear_auth_cookie() -> None:
    components.html(
        f"""
        <script>
        document.cookie = {json.dumps(COOKIE_NAME)} + "=; path=/; max-age=0; SameSite=Lax";
        </script>
        """,
        height=0,
        width=0,
    )


def persist_login(username: str) -> None:
    exp = int(time.time()) + MAX_AGE_SECONDS
    _set_auth_cookie(_sign(username.strip(), exp))


def clear_persisted_login() -> None:
    _clear_auth_cookie()
    st.session_state.pop("_cookie_restore_done", None)


def try_restore_session() -> None:
    """Restore st.session_state.user from signed cookie if missing."""
    if st.session_state.get("user"):
        return
    if st.session_state.get("_cookie_restore_done"):
        return

    st.session_state._cookie_restore_done = True
    raw = _read_request_cookies().get(COOKIE_NAME, "")
    if not raw:
        return

    username = _verify(unquote(raw))
    if not username:
        _clear_auth_cookie()
        return

    from utils.auth import _public_user
    from utils.data_store import get_user

    user = get_user(username)
    if not user:
        return
    if user.get("role") in ("pending", "removed"):
        return
    st.session_state.user = _public_user(user)
