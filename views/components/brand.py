"""KORE ATHLETIC brand assets and headers."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from utils.config import APP_NAME, APP_SUBTITLE, COACH_NAME

LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "logo.png"


def logo_exists() -> bool:
    return LOGO_PATH.exists()


def _logo_data_uri() -> str:
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return f"data:image/png;base64,{encoded}"


def _render_logo(*, framed: bool = False) -> None:
    """Internal: render logo image."""
    if not logo_exists():
        return
    if framed:
        st.markdown(
            f"""<div style="background:#0f1117;border-radius:10px;padding:8px;
            border:1px solid #334155;max-width:120px;">
            <img src="{_logo_data_uri()}" style="width:100%;display:block;border-radius:6px;" />
            </div>""",
            unsafe_allow_html=True,
        )
        return
    st.image(str(LOGO_PATH), use_container_width=True)


def render_logo(*, framed: bool = False) -> None:
    """Show the K logo; use framed=True on light backgrounds."""
    _render_logo(framed=framed)


def render_sidebar_brand(
    *,
    user_name: str = "訪客",
    role_label: str = "訪客",
    username: str | None = None,
) -> None:
    if logo_exists():
        _render_logo()
    else:
        st.markdown(f"### {APP_NAME}")

    st.markdown(
        f"<p style='margin:4px 0 0;font-size:13px;font-weight:700;color:#e2e8f0;"
        f"letter-spacing:0.06em;'>{APP_NAME}</p>",
        unsafe_allow_html=True,
    )
    if username:
        from views.components.avatar import person_row_html

        st.markdown(
            person_row_html(
                user_name,
                subtitle=role_label,
                username=username,
                size=32,
                dark=True,
            ),
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"{user_name} · {role_label}")


def render_brand_header(*, compact: bool = False) -> None:
    if logo_exists():
        c1, c2 = st.columns([1, 4] if not compact else [1, 3])
        with c1:
            _render_logo(framed=True)
        with c2:
            _header_text(compact=compact)
    else:
        _header_text(compact=compact, standalone=True)


def render_auth_brand(*, compact: bool = True) -> None:
    """Login/register header — compact by default for mobile-first."""
    if compact:
        if logo_exists():
            c1, c2, c3 = st.columns([1, 1.2, 1])
            with c2:
                st.markdown(
                    f"""<div style="text-align:center;margin-bottom:0.35rem;">
                    <img src="{_logo_data_uri()}" style="width:56px;display:inline-block;" />
                    </div>""",
                    unsafe_allow_html=True,
                )
        st.markdown(
            f"""<div style="text-align:center;margin-bottom:0.75rem;">
            <div style="font-size:1.15rem;font-weight:800;color:#0f172a;letter-spacing:0.06em;">
            {APP_NAME}</div>
            <div style="font-size:0.78rem;color:#64748b;">{APP_SUBTITLE}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        return
    if logo_exists():
        _, mid, _ = st.columns([1, 1.2, 1])
        with mid:
            st.markdown(
                f"""<div style="background:#0f1117;border-radius:12px;padding:12px;
                border:1px solid #334155;text-align:center;margin-bottom:0.5rem;">
                <img src="{_logo_data_uri()}" style="width:100%;max-width:160px;display:inline-block;" />
                </div>""",
                unsafe_allow_html=True,
            )
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#0f1117,#1a1d24);
        border:1px solid #334155;border-radius:12px;padding:1.25rem;text-align:center;
        color:#f8fafc;margin-bottom:1rem;">
        <h2 style="margin:0.25rem 0;font-weight:800;letter-spacing:0.08em;">{APP_NAME}</h2>
        <p style="margin:0;font-size:0.9rem;color:#94a3b8;">{APP_SUBTITLE}</p></div>""",
        unsafe_allow_html=True,
    )


def _header_text(*, compact: bool = False, standalone: bool = False) -> None:
    pad = "0.85rem 1rem" if compact else "1rem 1.25rem"
    title_size = "1.15rem" if compact else "1.45rem"
    if standalone:
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#0f1117,#1a1d24);
            border:1px solid #334155;color:#f8fafc;padding:{pad};border-radius:12px;
            margin-bottom:1rem;">
            <h1 style="margin:0;font-size:{title_size};font-weight:900;letter-spacing:0.08em;">
            {APP_NAME}</h1>
            <p style="margin:0.25rem 0 0;font-size:0.85rem;color:#94a3b8;">{APP_SUBTITLE}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""<div style="padding-top:0.25rem;">
        <h1 style="margin:0;font-size:{title_size};font-weight:900;letter-spacing:0.08em;
        color:#0f172a;">{APP_NAME}</h1>
        <p style="margin:0.25rem 0 0;font-size:0.85rem;color:#64748b;">{APP_SUBTITLE}</p>
        <p style="margin:0.15rem 0 0;font-size:0.75rem;color:#94a3b8;">{COACH_NAME} 教練</p>
        </div>""",
        unsafe_allow_html=True,
    )
