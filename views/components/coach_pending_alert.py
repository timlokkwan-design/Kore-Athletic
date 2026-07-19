"""Sidebar alert + mobile popup for coach pending approvals."""
from __future__ import annotations

import streamlit as st

from utils.coach_pending import (
    get_coach_pending_lines,
    get_coach_pending_summary,
    get_coach_pending_total,
    pending_fingerprint,
)


def navigate_to_coach_pending() -> None:
    st.session_state["main_page"] = "教練平台"
    st.session_state["coach_section"] = "隊伍管理"
    st.session_state["coach_team_tab"] = "待審事項"


def _already_on_pending_page() -> bool:
    return (
        st.session_state.get("main_page") == "教練平台"
        and st.session_state.get("coach_section") == "隊伍管理"
        and st.session_state.get("coach_team_tab") == "待審事項"
    )


def render_coach_pending_sidebar() -> None:
    total = get_coach_pending_total()
    if total <= 0:
        st.session_state.pop("_coach_pending_dismissed_fp", None)
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


def render_coach_pending_mobile_banner() -> None:
    """Always-visible main-area banner (sidebar is collapsed on phones)."""
    total = get_coach_pending_total()
    if total <= 0 or _already_on_pending_page():
        return

    lines = get_coach_pending_lines()
    detail = "、".join(f"{label} {count}" for label, count in lines)
    st.markdown(
        f"""<div class="ka-pending-mobile-banner" role="alert">
        <div class="ka-pending-mobile-banner-title">⏳ 有 {total} 項待審批</div>
        <div class="ka-pending-mobile-banner-detail">{detail}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button(
        "立即前往審批",
        key="coach_pending_mobile_banner_go",
        type="primary",
        use_container_width=True,
    ):
        navigate_to_coach_pending()
        st.rerun()


def maybe_show_coach_pending_popup() -> None:
    """Pop a dialog whenever any approval is waiting (especially on mobile).

    Shows when:
    - coach just logged in and anything is pending, or
    - pending fingerprint differs from the last dismissed one

    Skips while coach is already on the pending-approvals tab.
    """
    force = bool(st.session_state.get("_fresh_login"))
    summary = get_coach_pending_summary(force_refresh=force)
    total = sum(int(v) for v in summary.values())
    if total <= 0:
        st.session_state.pop("_coach_pending_dismissed_fp", None)
        return

    if _already_on_pending_page():
        return

    fp = pending_fingerprint(summary)
    dismissed = st.session_state.get("_coach_pending_dismissed_fp")
    if not force and dismissed == fp:
        return

    lines = get_coach_pending_lines()
    detail = "、".join(f"{label} {count}" for label, count in lines)

    @st.dialog("⏳ 有待審批事項", width="small")
    def _popup() -> None:
        st.markdown(f"目前共有 **{total}** 項待你處理：")
        st.info(detail or "請前往隊伍管理 → 待審事項")
        if st.button(
            "前往審批",
            type="primary",
            use_container_width=True,
            key="coach_pending_popup_go",
        ):
            st.session_state["_coach_pending_dismissed_fp"] = fp
            navigate_to_coach_pending()
            st.rerun()
        if st.button(
            "稍後處理",
            use_container_width=True,
            key="coach_pending_popup_later",
        ):
            st.session_state["_coach_pending_dismissed_fp"] = fp
            st.rerun()

    _popup()
