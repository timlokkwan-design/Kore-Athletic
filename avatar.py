"""Student avatar display and upload helpers."""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import streamlit as st

from utils.data_store import get_avatar_path, get_user_by_name, load_users
from utils.helpers import safe_str


def _initials(name: str) -> str:
    text = safe_str(name).strip()
    if len(text) >= 2:
        return text[:2]
    return text[:1] or "?"


def _mime_for_path(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "image/png"


@st.cache_data(show_spinner=False)
def _cached_data_uri(path_str: str, mtime_ns: int) -> str:
    path = Path(path_str)
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{_mime_for_path(path)};base64,{encoded}"


@st.cache_data(show_spinner=False, ttl=30)
def _name_to_username_map() -> dict[str, str]:
    users = load_users()
    if users.empty:
        return {}
    return {
        safe_str(row["name"]): safe_str(row["username"])
        for row in users.to_dict("records")
        if safe_str(row.get("name"))
    }


def clear_avatar_cache() -> None:
    _cached_data_uri.clear()
    _name_to_username_map.clear()


def resolve_username(*, username: str | None = None, name: str | None = None) -> str:
    if username:
        return safe_str(username)
    if name:
        mapped = _name_to_username_map().get(safe_str(name))
        if mapped:
            return mapped
        user = get_user_by_name(name)
        if user:
            return safe_str(user.get("username"))
    return ""


def avatar_data_uri(*, username: str | None = None, name: str | None = None) -> str | None:
    resolved = resolve_username(username=username, name=name)
    path = get_avatar_path(username=resolved or None, name=name if not resolved else None)
    if not path or not path.exists():
        return None
    uri = _cached_data_uri(str(path.resolve()), path.stat().st_mtime_ns)
    return uri or None


def avatar_html(*, name: str | None = None, username: str | None = None, size: int = 40) -> str:
    display_name = safe_str(name) or safe_str(username) or "?"
    uri = avatar_data_uri(username=username, name=name)
    if uri:
        return (
            f'<img src="{uri}" alt="{display_name}" '
            f'style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;'
            f'border:2px solid #e2e8f0;flex-shrink:0;display:block;" />'
        )
    font = max(10, size // 3)
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:linear-gradient(135deg,#64748b,#475569);color:#f8fafc;'
        f'display:flex;align-items:center;justify-content:center;font-size:{font}px;'
        f'font-weight:700;flex-shrink:0;border:2px solid #e2e8f0;">{_initials(display_name)}</div>'
    )


def person_row_html(
    name: str,
    *,
    subtitle: str = "",
    username: str | None = None,
    size: int = 36,
    bold: bool = True,
    dark: bool = False,
) -> str:
    name_color = "#e2e8f0" if dark else "#0f172a"
    label = f"<span style='color:{name_color};font-weight:700;'>{name}</span>" if bold else name
    sub_color = "#94a3b8" if dark else "#64748b"
    sub = (
        f"<div style='font-size:0.82rem;color:{sub_color};margin-top:2px;'>{subtitle}</div>"
        if subtitle
        else ""
    )
    return (
        f"<div style='display:flex;align-items:center;gap:10px;'>"
        f"{avatar_html(name=name, username=username, size=size)}"
        f"<div style='line-height:1.25;'>{label}{sub}</div></div>"
    )


def athlete_card_html(
    name: str,
    body_html: str,
    *,
    username: str | None = None,
    bg: str = "#f8fafc",
    border: str = "#e2e8f0",
    size: int = 48,
) -> str:
    return (
        f"<div style='background:{bg};padding:1rem;border-radius:10px;border:1px solid {border};'>"
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;'>"
        f"{avatar_html(name=name, username=username, size=size)}"
        f"<b style='font-size:1rem;'>{name}</b></div>{body_html}</div>"
    )


def render_avatar(*, name: str | None = None, username: str | None = None, size: int = 64) -> None:
    st.markdown(avatar_html(name=name, username=username, size=size), unsafe_allow_html=True)


def render_person(
    name: str,
    *,
    subtitle: str = "",
    username: str | None = None,
    size: int = 36,
) -> None:
    st.markdown(
        person_row_html(name, subtitle=subtitle, username=username, size=size),
        unsafe_allow_html=True,
    )
