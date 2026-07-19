"""KORE ATHLETIC — V6 full navigation."""
from __future__ import annotations

import sys
from pathlib import Path

# Streamlit Cloud: if repo has kore-athletic/ subfolder, use it for imports
_app_dir = Path(__file__).resolve().parent
if not (_app_dir / "utils").is_dir():
    _nested = _app_dir / "kore-athletic"
    if (_nested / "utils").is_dir():
        sys.path.insert(0, str(_nested))

import streamlit as st

from utils.auth import get_current_user, logout
from utils.config import APP_NAME, APP_VERSION
from utils.coach_pending import get_coach_pending_total
from utils.data_store import init_sample_data
from utils.nav_persist import clear_nav_state, save_nav_state, try_restore_nav_state
from utils.session_cache import soft_refresh_data
from utils.session_persist import refresh_persisted_login, try_restore_session
from utils.site_content import is_pb_public
from views.analysis_view import render_analysis
from views.auth_view import render_auth_view
from views.coach_view import COACH_NAV_CATEGORIES, COACH_SECTIONS, render_coach_view
from views.components.brand import LOGO_PATH, logo_exists, render_brand_header, render_sidebar_brand
from views.components.coach_pending_alert import (
    maybe_show_coach_pending_popup,
    render_coach_pending_mobile_banner,
    render_coach_pending_sidebar,
)
from views.components.sidebar_nav import render_nav_categories, render_top_nav
from views.components.pwa import inject_pwa_head, render_pwa_install_hint
from views.components.mobile_nav import render_visitor_sidebar_nav
from views.components.theme import inject_global_css, render_breadcrumb, render_theme_toggle
from views.leaderboard_view import render_leaderboard
from views.parent_view import render_parent_view
from views.register_view import render_register_view
from views.student_view import STUDENT_NAV_CATEGORIES, STUDENT_SECTIONS, render_student_view
from views.visitor_view import render_visitor_view

st.set_page_config(
    page_title=f"{APP_NAME} | 田徑訓練管理",
    page_icon=str(LOGO_PATH) if logo_exists() else "🏃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "initialized" not in st.session_state:
    init_sample_data()
    st.session_state.initialized = True
    # 預載常用資料到 session 快取，減少按鈕後等待
    from utils.data_store import load_periodization, load_programs, load_users

    load_users()
    load_programs()
    load_periodization()

if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "light"

ROLE_LABELS = {"coach": "教練", "student": "學員", "parent": "家長", "visitor": "訪客"}

TOP_NAV = {
    "coach": [
        ("🎯 教練平台", "教練平台"),
        ("🏆 PB 排行榜", "PB 排行榜"),
        ("📊 成效分析", "成效分析"),
    ],
    "student": [
        ("🏃 學生平台", "學生平台"),
        ("🏆 PB 排行榜", "PB 排行榜"),
    ],
    "parent": [
        ("👨‍👩‍👧 家長專區", "家長專區"),
        ("🏆 PB 排行榜", "PB 排行榜"),
    ],
}


def _visitor_nav() -> list[tuple[str, str]]:
    nav = [
        ("🏠 訪客專區", "訪客專區"),
        ("🔑 登入", "登入"),
        ("📝 註冊", "註冊新學員"),
    ]
    if is_pb_public():
        nav.append(("🏆 PB榜", "PB 排行榜"))
    return nav


def _category_for_section(categories: list[tuple[str, list[str]]], section: str) -> str | None:
    for cat_label, items in categories:
        if section in items:
            return cat_label
    return None


def _render_page(
    page: str,
    role: str,
    *,
    coach_section: str | None = None,
    student_section: str | None = None,
) -> None:
    if page == "訪客專區":
        render_visitor_view()
    elif page == "登入":
        render_auth_view()
    elif page == "註冊新學員":
        render_register_view()
    elif page == "教練平台":
        render_coach_view(coach_section or COACH_SECTIONS[0])
    elif page == "學生平台":
        render_student_view(student_section or STUDENT_SECTIONS[0])
    elif page == "家長專區":
        render_parent_view()
    elif page == "PB 排行榜":
        render_leaderboard()
    elif page == "成效分析":
        render_analysis()


def main() -> None:
    try_restore_session()
    user = get_current_user()
    role = user["role"] if user else "visitor"
    try_restore_nav_state(role)

    inject_global_css()
    inject_pwa_head()

    if role == "visitor":
        top_options = _visitor_nav()
        default_page = "訪客專區"
    else:
        top_options = TOP_NAV.get(role, _visitor_nav())
        default_page = top_options[0][1]

    with st.sidebar:
        render_sidebar_brand(
            user_name=user["name"] if user else "訪客",
            role_label=ROLE_LABELS.get(role, role),
            username=user.get("username") if user and role == "student" else None,
        )
        st.markdown("---")
        if role == "coach":
            render_theme_toggle()
            st.markdown("---")
        if role == "coach":
            render_coach_pending_sidebar()
        if role == "visitor":
            page = render_visitor_sidebar_nav(top_options, "main_page", default_page)
        elif role != "visitor":
            st.markdown("<p class='ka-nav-label'>主選單</p>", unsafe_allow_html=True)
            page = render_top_nav(top_options, "main_page", default_page)

        coach_section = None
        student_section = None
        if role == "coach" and page == "教練平台":
            if st.session_state.get("coach_section") == "週期化課表":
                st.session_state.coach_section = "設定課表"
            st.markdown("---")
            pending_total = get_coach_pending_total()
            nav_badges = {"隊伍管理": pending_total} if pending_total else None
            coach_section = render_nav_categories(
                COACH_NAV_CATEGORIES,
                "coach_section",
                COACH_SECTIONS[0],
                badges=nav_badges,
            )
        elif role == "student" and page == "學生平台":
            st.markdown("---")
            student_section = render_nav_categories(
                STUDENT_NAV_CATEGORIES,
                "student_section",
                STUDENT_SECTIONS[0],
            )

        st.markdown("---")
        if role == "coach":
            st.caption(f"v{APP_VERSION}")
        if user:
            if st.button("🔄 重新整理", use_container_width=True, key="soft_refresh_btn"):
                soft_refresh_data()
            if st.button("登出", use_container_width=True):
                logout()
                st.rerun()

    if role in ("visitor", "student"):
        render_pwa_install_hint()

    if role == "coach":
        # Popup first (covers login / new pending); banner stays visible on phone
        # even after "稍後處理", since the sidebar is collapsed by default.
        maybe_show_coach_pending_popup()
        render_coach_pending_mobile_banner()

    visitor_public_pages = ("訪客專區", "登入", "註冊新學員")
    if is_pb_public():
        visitor_public_pages = (*visitor_public_pages, "PB 排行榜")

    if role == "visitor" and page == "PB 排行榜" and not is_pb_public():
        render_breadcrumb("PB 排行榜")
        st.warning("PB 排行榜只供登入用戶查看。請點選單（☰）→「登入」。")
        render_auth_view()
        return

    if role == "visitor" and page not in visitor_public_pages:
        st.warning("請先登入或使用訪客專區")
        render_visitor_view()
        return

    if role == "visitor" and page == "PB 排行榜" and is_pb_public():
        render_brand_header()

    if user and page == "登入":
        page = {"coach": "教練平台", "student": "學生平台", "parent": "家長專區"}.get(role, "PB 排行榜")

    if user and page == "教練平台" and coach_section:
        cat = _category_for_section(COACH_NAV_CATEGORIES, coach_section or "")
        parts = [page, cat, coach_section] if cat else [page, coach_section or ""]
        render_breadcrumb(*[p for p in parts if p])
    elif user and page == "學生平台" and student_section:
        cat = _category_for_section(STUDENT_NAV_CATEGORIES, student_section or "")
        parts = [page, cat, student_section] if cat else [page, student_section or ""]
        render_breadcrumb(*[p for p in parts if p])
    elif page == "訪客專區":
        pass
    elif page in ("登入", "註冊新學員"):
        pass
    elif user and page not in ("登入", "註冊新學員"):
        render_breadcrumb(page)

    if role == "coach" and page == "教練平台":
        _render_page(page, role, coach_section=coach_section or COACH_SECTIONS[0])
    elif role == "student" and page == "學生平台":
        _render_page(page, role, student_section=student_section or STUDENT_SECTIONS[0])
    else:
        _render_page(page, role)

    if user:
        save_nav_state(
            role,
            main_page=page,
            coach_section=coach_section,
            student_section=student_section,
        )
        # Keep cookie / localStorage alive so pull-to-refresh does not log out
        refresh_persisted_login()

    st.session_state.pop("_fresh_login", None)


if __name__ == "__main__":
    main()
