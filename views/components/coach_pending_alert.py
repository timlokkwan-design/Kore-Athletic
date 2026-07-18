"""Sidebar alert for coach pending approvals."""
from __future__ import annotations

import streamlit as st

from utils.coach_pending import get_coach_pending_lines, get_coach_pending_total


def navigate_to_coach_pending() -> None:
    st.session_state["main_page"] = "教練平台"
    st.session_state["coach_section"] = "隊伍管理"
    st.session_state["coach_team_tab"] = "待審事項"


def render_coach_pending_sidebar() -> None:
    total = get_coach_pending_total()
    if total <= 0:
        return

    lines = get_coach_pending_lines()
    items_html = "".join(
        f'<li><span>{label}</span><strong>{count}</strong></li>'
        for label, count in lines
    )
    st.markdown(
        f"""<div class="ka-sidebar-pending">
        <div class="ka-sidebar-pending-title">⏳ 待審通知 <span class="ka-sidebar-pending-badge">{total}</span></div>
        <ul class="ka-sidebar-pending-list">{items_html}</ul>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button(
        "立即審批",
        key="coach_pending_go",
        type="primary",
        use_container_width=True,
    ):
        navigate_to_coach_pending()
        st.rerun()
