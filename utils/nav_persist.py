"""Remember last page/section in localStorage (PWA-friendly)."""

from __future__ import annotations

import json
from urllib.parse import unquote

import streamlit as st
import streamlit.components.v1 as components

from utils.browser_storage import browser_storage_js

LS_NAV_KEY = "ka_nav_state"
BRIDGE_COOKIE = "ka_nav_bridge"
AUTH_PAGES = frozenset({"登入", "註冊新學員", "訪客專區"})


def _parent_js() -> str:
    return browser_storage_js()


def _read_request_cookies() -> dict[str, str]:
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
        if not raw:
            return {}
        out: dict[str, str] = {}
        for part in raw.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                out[k.strip()] = v.strip()
        return out
    except Exception:
        return {}


def _clear_nav_bridge_cookie() -> None:
    components.html(
        f"""
        <script>
        (function() {{
            {_parent_js()}
            _kaDoc.cookie = {json.dumps(BRIDGE_COOKIE)} + "=; path=/; max-age=0; SameSite=Lax" + _kaSecure;
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def _inject_nav_bridge() -> None:
    components.html(
        f"""
        <script>
        (function() {{
            {_parent_js()}
            const BRIDGE = {json.dumps(BRIDGE_COOKIE)};
            const LS = {json.dumps(LS_NAV_KEY)};
            const hasBridge = _kaDoc.cookie.split(';').some(
                c => c.trim().startsWith(BRIDGE + '=')
            );
            if (hasBridge) return;
            const raw = _kaLs.getItem(LS);
            if (!raw) return;
            _kaDoc.cookie = BRIDGE + "=" + encodeURIComponent(raw)
                + "; path=/; max-age=120; SameSite=Lax" + _kaSecure;
            try {{ window.top.location.reload(); }} catch (e) {{ window.parent.location.reload(); }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def _apply_nav_payload(data: dict, role: str) -> None:
    if data.get("role") != role:
        return
    main_page = data.get("main_page")
    if isinstance(main_page, str) and main_page.strip():
        mp = main_page.strip()
        if role == "visitor" or mp not in AUTH_PAGES:
            st.session_state.main_page = mp
    if role == "coach":
        from views.coach_view import COACH_SECTIONS

        sec = data.get("coach_section")
        if isinstance(sec, str) and sec in COACH_SECTIONS:
            st.session_state.coach_section = sec
    elif role == "student":
        from views.student_view import STUDENT_SECTIONS

        sec = data.get("student_section")
        if isinstance(sec, str) and sec in STUDENT_SECTIONS:
            st.session_state.student_section = sec
    theme = data.get("ui_theme")
    if theme in ("light", "dark"):
        st.session_state.ui_theme = theme
        st.session_state.ui_theme_toggle = theme == "dark"


def try_restore_nav_state(role: str) -> None:
    """Restore main_page / section from localStorage (via one-time cookie bridge)."""
    if role == "visitor":
        return
    if st.session_state.get("_nav_restored"):
        return

    bridge_raw = _read_request_cookies().get(BRIDGE_COOKIE, "")
    if bridge_raw:
        st.session_state._nav_restored = True
        try:
            data = json.loads(unquote(bridge_raw))
            if isinstance(data, dict):
                _apply_nav_payload(data, role)
        except json.JSONDecodeError:
            pass
        _clear_nav_bridge_cookie()
        return

    if st.session_state.get("_nav_bridge_injected"):
        st.session_state._nav_restored = True
        return

    st.session_state._nav_bridge_injected = True
    _inject_nav_bridge()


def save_nav_state(
    role: str,
    *,
    main_page: str | None = None,
    coach_section: str | None = None,
    student_section: str | None = None,
) -> None:
    """Write current navigation to localStorage."""
    if role == "visitor":
        return
    payload = {
        "role": role,
        "main_page": main_page or st.session_state.get("main_page", ""),
        "coach_section": coach_section or st.session_state.get("coach_section", ""),
        "student_section": student_section or st.session_state.get("student_section", ""),
        "ui_theme": st.session_state.get("ui_theme", "light"),
    }
    encoded = json.dumps(payload, ensure_ascii=False)
    components.html(
        f"""
        <script>
        (function() {{
            {_parent_js()}
            _kaLs.setItem({json.dumps(LS_NAV_KEY)}, {json.dumps(encoded)});
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def clear_nav_state() -> None:
    components.html(
        f"""
        <script>
        (function() {{
            {_parent_js()}
            _kaLs.removeItem({json.dumps(LS_NAV_KEY)});
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
