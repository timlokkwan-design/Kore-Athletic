"""Coach view — sidebar-driven sections."""

import streamlit as st

from views.coach_sections import (
    render_coach_comm,
    render_coach_comp,
    render_coach_program,
    render_coach_team,
    render_coach_video,
    render_coach_wellness,
)
from views.coach_attendance_section import render_coach_attendance
from views.coach_comp_registration_section import render_coach_comp_registration
from views.coach_dashboard_section import render_coach_dashboard
from views.coach_schedule_section import render_coach_schedule
from views.coach_site_settings_section import render_coach_site_settings
from views.components.competition_schedule import render_coach_competition_schedule
from views.components.mobile_nav import render_coach_bottom_dock
from views.components.theme import render_page_header

COACH_NAV_CATEGORIES: list[tuple[str, list[str]]] = [
    ("📊 總覽", ["總覽"]),
    ("📅 訓練規劃", ["設定課表", "訓練時間表"]),
    ("👥 隊伍與健康", ["出席表", "ACWR/健康", "隊伍管理"]),
    ("🏅 比賽事務", ["賽事時間表", "比賽報名表", "比賽管理"]),
    ("🎬 分析與溝通", ["影片分析", "家長溝通"]),
    ("⚙️ 系統設定", ["網站內容"]),
]

COACH_SECTIONS = [item for _, items in COACH_NAV_CATEGORIES for item in items]

_SECTION_RENDERERS = {
    "總覽": render_coach_dashboard,
    "設定課表": render_coach_program,
    "訓練時間表": render_coach_schedule,
    "出席表": render_coach_attendance,
    "ACWR/健康": render_coach_wellness,
    "隊伍管理": render_coach_team,
    "賽事時間表": render_coach_competition_schedule,
    "比賽報名表": render_coach_comp_registration,
    "比賽管理": render_coach_comp,
    "影片分析": render_coach_video,
    "家長溝通": render_coach_comm,
    "網站內容": render_coach_site_settings,
}


def render_coach_view(section: str) -> None:
    from utils.auth import require_coach_or_stop
    require_coach_or_stop()
    render_page_header("教練平台", f"目前分頁：{section}")
    render_coach_bottom_dock(section)

    renderer = _SECTION_RENDERERS.get(section, render_coach_dashboard)
    renderer()
