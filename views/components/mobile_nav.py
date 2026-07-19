"""Mobile-first navigation — student quick dock & visitor sidebar."""
from __future__ import annotations

import streamlit as st


def _set_main_page(session_key: str, page: str) -> None:
    st.session_state[session_key] = page


def _set_student_section(section: str) -> None:
    st.session_state["student_section"] = section


def render_visitor_sidebar_nav(
    options: list[tuple[str, str]],
    session_key: str,
    default: str,
) -> str:
    """Visitor navigation inside sidebar (replaces main-area top buttons)."""
    values = [val for _, val in options]
    if session_key not in st.session_state or st.session_state[session_key] not in values:
        st.session_state[session_key] = default

    st.markdown("<p class='ka-nav-label'>瀏覽</p>", unsafe_allow_html=True)
    current = st.session_state[session_key]
    for label, val in options:
        st.button(
            label,
            key=f"vis_nav_{val}",
            use_container_width=True,
            type="primary" if current == val else "secondary",
            on_click=_set_main_page,
            args=(session_key, val),
        )
    return st.session_state[session_key]


def render_student_quick_dock(current_section: str) -> None:
    """Fixed-style quick actions for high-frequency student tasks."""
    st.markdown('<div class="ka-student-dock-marker"></div>', unsafe_allow_html=True)
    items = [
        ("📅 課表", "訓練時間表"),
        ("✅ 簽到", "出席"),
        ("📝 日誌", "訓練日誌"),
        ("🏅 比賽", "賽事時間表"),
    ]
    cols = st.columns(len(items))
    for col, (label, section) in zip(cols, items):
        with col:
            st.button(
                label,
                key=f"stu_dock_{section}",
                use_container_width=True,
                type="primary" if current_section == section else "secondary",
                on_click=_set_student_section,
                args=(section,),
            )
