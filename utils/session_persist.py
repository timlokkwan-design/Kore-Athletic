"""Persist login across refresh: JWT cookie + localStorage backup (PWA-friendly).

Uses streamlit-extras CookieManager (reads cookies after page load) and
st.html(..., unsafe_allow_javascript=True) so writes run in the parent page —
not a sandboxed components.html iframe (which often fails on Streamlit Cloud).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from urllib.parse import unquote

import streamlit as st
import streamlit.components.v1 as components

from utils.browser_storage import browser_storage_js, clear_browser_cookie_js, set_browser_cookie_js

COOKIE_NAME = "ka_auth"
LS_KEY = "ka_auth_session"
DEFAULT_SESSION_DAYS = 30
_CM_WIDGET_KEY = "ka_auth_cm"
_CM_STATE_KEY = "_ka_cookie_manager"
_CM_WAIT_KEY = "_ka_cm_wait"


def _cookie_secret() -> str:
    try:
        secret = st.secrets.get("auth", {}).get("cookie_secret", "")
        if secret:
            return str(secret)
    except Exception:
        pass
    return "kore-athletic-dev-cookie-secret-change-me"


def session_max_age_seconds() -> int:
    """Login persistence duration; default 30 days, configurable 14/30 via secrets."""
    try:
        days = int(st.secrets.get("auth", {}).get("session_days", DEFAULT_SESSION_DAYS))
    except (TypeError, ValueError):
        days = DEFAULT_SESSION_DAYS
    days = max(1, min(days, 90))
    return days * 24 * 60 * 60


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    pad = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + pad)


def make_auth_token(username: str, exp: int) -> str:
    """HS256 JWT: sub=username, exp=unix timestamp."""
    secret = _cookie_secret()
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64url(json.dumps({"sub": username.strip(), "exp": exp}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}".encode()
    sig = _b64url(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def _verify_legacy_pipe_token(token: str) -> str | None:
    """Legacy username|exp|hmac format (kept for existing cookies)."""
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


def verify_auth_token(token: str) -> str | None:
    """Verify JWT or legacy pipe token; return username or None."""
    token = str(token).strip()
    if not token:
        return None
    if token.count(".") == 2:
        header_b64, payload_b64, sig_b64 = token.split(".", 2)
        try:
            payload = json.loads(_b64url_decode(payload_b64))
            exp = int(payload.get("exp", 0))
            username = str(payload.get("sub", "")).strip()
        except (ValueError, json.JSONDecodeError, TypeError):
            return _verify_legacy_pipe_token(token)
        if not username or exp < int(time.time()):
            return None
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected = _b64url(hmac.new(_cookie_secret().encode(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(sig_b64, expected):
            return None
        return username
    return _verify_legacy_pipe_token(token)


def _run_browser_js(script_body: str) -> None:
    """Execute JS on the parent Streamlit page (not a sandboxed iframe)."""
    html = f"<script>(function(){{\n{script_body}\n}})();</script>"
    try:
        st.html(html, unsafe_allow_javascript=True)
    except TypeError:
        components.html(html, height=0, width=0)
    except Exception:
        try:
            components.html(html, height=0, width=0)
        except Exception:
            pass


def init_auth_persistence() -> None:
    """Mount CookieManager once per script run. Call at the start of main()."""
    try:
        from streamlit_extras.cookie_manager import CookieManager

        st.session_state[_CM_STATE_KEY] = CookieManager(key=_CM_WIDGET_KEY)
    except Exception:
        st.session_state[_CM_STATE_KEY] = None


def _cookie_manager():
    return st.session_state.get(_CM_STATE_KEY)


def _cm_set_cookie(token: str, max_age: int) -> None:
    cm = _cookie_manager()
    if cm is None:
        return
    try:
        cm.set(
            COOKIE_NAME,
            token,
            max_age=max_age,
            path="/",
            secure=True,
            samesite="lax",
        )
    except Exception:
        pass


def _cm_delete_cookie() -> None:
    cm = _cookie_manager()
    if cm is None:
        return
    try:
        cm.delete(COOKIE_NAME, path="/", secure=True, samesite="lax")
    except Exception:
        pass


def _cm_get_cookie() -> str:
    cm = _cookie_manager()
    if cm is None or not getattr(cm, "ready", lambda: False)():
        return ""
    try:
        value = cm.get(COOKIE_NAME)
    except Exception:
        return ""
    return str(value or "").strip()


def _inject_storage_bridge() -> None:
    """
    If cookie missing but localStorage has a valid session, copy token to cookie
    and reload once (parent-page JS — works on desktop F5 / Streamlit Cloud).
    """
    if st.session_state.get("_storage_bridge_done"):
        return
    st.session_state._storage_bridge_done = True

    max_age = session_max_age_seconds()
    _run_browser_js(
        f"""
        {browser_storage_js()}
        const COOKIE = {json.dumps(COOKIE_NAME)};
        const LS = {json.dumps(LS_KEY)};
        const hasCookie = _kaDoc.cookie.split(';').some(
            c => c.trim().startsWith(COOKIE + '=')
        );
        if (hasCookie) return;
        const raw = _kaLs.getItem(LS);
        if (!raw) return;
        let data;
        try {{ data = JSON.parse(raw); }} catch (e) {{
            _kaLs.removeItem(LS);
            return;
        }}
        if (data.expiresAt && Date.now() > data.expiresAt) {{
            _kaLs.removeItem(LS);
            return;
        }}
        const token = data.token;
        if (!token) return;
        const maxAge = Math.max(
            60,
            Math.floor((data.expiresAt - Date.now()) / 1000) || {max_age}
        );
        _kaDoc.cookie = COOKIE + "=" + encodeURIComponent(token)
            + "; path=/; max-age=" + maxAge + "; SameSite=Lax" + _kaSecure;
        try {{ window.location.reload(); }} catch (e) {{
            try {{ window.top.location.reload(); }} catch (e2) {{}}
        }}
        """
    )


def _persist_client_storage(token: str, username: str, exp: int) -> None:
    max_age = session_max_age_seconds()
    _cm_set_cookie(token, max_age)
    expires_at_ms = exp * 1000
    ui_theme = st.session_state.get("ui_theme", "light")
    ls_payload = json.dumps({
        "token": token,
        "username": username,
        "expiresAt": expires_at_ms,
        "ui_theme": ui_theme,
    })
    _run_browser_js(
        f"""
        {set_browser_cookie_js(COOKIE_NAME, token, max_age)}
        {browser_storage_js()}
        _kaLs.setItem({json.dumps(LS_KEY)}, {json.dumps(ls_payload)});
        """
    )


def _clear_client_storage() -> None:
    _cm_delete_cookie()
    _run_browser_js(
        f"""
        {clear_browser_cookie_js(COOKIE_NAME)}
        {browser_storage_js()}
        _kaLs.removeItem({json.dumps(LS_KEY)});
        """
    )


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


def persist_login(username: str) -> None:
    name = username.strip()
    exp = int(time.time()) + session_max_age_seconds()
    token = make_auth_token(name, exp)
    _persist_client_storage(token, name, exp)
    st.session_state._auth_token_username = name
    st.session_state._auth_token_exp = exp


def refresh_persisted_login() -> None:
    """Re-write cookie/localStorage for the current user (survives pull-to-refresh)."""
    user = st.session_state.get("user")
    if not user:
        return
    username = str(user.get("username") or "").strip()
    if not username:
        return
    # Avoid flooding browser writes every widget interaction — refresh at most every 10 min
    now = int(time.time())
    last = int(st.session_state.get("_auth_persist_touch", 0) or 0)
    exp = int(st.session_state.get("_auth_token_exp", 0) or 0)
    if last and (now - last) < 600 and exp > now + 3600:
        return
    persist_login(username)
    st.session_state._auth_persist_touch = now


def clear_persisted_login() -> None:
    _clear_client_storage()
    st.session_state.pop("_cookie_restore_done", None)
    st.session_state.pop("_storage_bridge_done", None)
    st.session_state.pop("_auth_persist_touch", None)
    st.session_state.pop("_auth_token_username", None)
    st.session_state.pop("_auth_token_exp", None)
    st.session_state.pop(_CM_WAIT_KEY, None)


def _restore_user(username: str) -> bool:
    from utils.auth import _public_user
    from utils.data_store import get_user

    user = get_user(username)
    if not user:
        return False
    if user.get("role") in ("pending", "removed"):
        return False
    st.session_state.user = _public_user(user)
    return True


def session_days() -> int:
    return max(1, session_max_age_seconds() // (24 * 60 * 60))


def session_persist_hint() -> str:
    days = session_days()
    return f"登入後將保持登入狀態 **{days} 天**（關閉分頁或重新整理仍有效）"


def try_restore_session() -> None:
    """Restore st.session_state.user from JWT cookie / localStorage backup."""
    if st.session_state.get("user"):
        return
    if st.session_state.get("_fresh_login"):
        return

    # Parent-page bridge: localStorage → cookie → reload (if needed)
    _inject_storage_bridge()

    cm = _cookie_manager()
    if cm is not None and not cm.ready():
        # Wait a few auto-reruns for CookieManager to sync browser cookies.
        waits = int(st.session_state.get(_CM_WAIT_KEY, 0) or 0)
        if waits < 5:
            st.session_state[_CM_WAIT_KEY] = waits + 1
            # Stop before rendering as visitor; component ready → auto-rerun.
            st.stop()
    else:
        st.session_state.pop(_CM_WAIT_KEY, None)

    raw = _cm_get_cookie() or _read_request_cookies().get(COOKIE_NAME, "")
    if not raw:
        return

    username = verify_auth_token(unquote(raw))
    if not username:
        clear_persisted_login()
        return

    if _restore_user(username):
        st.session_state._cookie_restore_done = True
        st.session_state._auth_token_username = username
        # Force refresh_persisted_login to renew cookie/localStorage soon
        st.session_state._auth_persist_touch = 0
        return
    clear_persisted_login()
