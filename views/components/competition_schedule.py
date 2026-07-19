"""Competition schedule — coach entry + student preview (賽事預告)."""
from __future__ import annotations

from datetime import date

import streamlit as st

from utils.data_store import (
    add_schedule_competition,
    delete_competition,
    ensure_season_competition_schedule,
    get_competition_schedule,
    get_competitions,
)
from utils.helpers import format_timetable_date, safe_str
from views.components.theme import render_empty_state


def _days_until(ds: str) -> int | None:
    try:
        return (date.fromisoformat(ds[:10]) - date.today()).days
    except ValueError:
        return None


def _render_schedule_list(comps: list[dict], *, show_delete: bool = False) -> None:
    if not comps:
        render_empty_state("暫無賽事預告", "教練加入比賽日期與名稱後會顯示於此")
        return
    for comp in comps:
        ds = safe_str(comp.get("date"))
        name = safe_str(comp.get("name")) or "未命名賽事"
        loc = safe_str(comp.get("location"))
        days = _days_until(ds)
        if days is None:
            when = format_timetable_date(ds) if ds else "—"
        elif days == 0:
            when = f"{format_timetable_date(ds)} · 今日"
        elif days > 0:
            when = f"{format_timetable_date(ds)} · 還有 {days} 天"
        else:
            when = f"{format_timetable_date(ds)} · 已結束"

        notes = safe_str(comp.get("notes"))
        detail = when + (f" · {loc}" if loc else "")
        if notes and notes not in ("賽事預告",):
            detail = f"{notes} · {detail}" if when else notes

        if show_delete:
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{name}**")
                st.caption(detail)
            with right:
                if st.button("刪除", key=f"comp_sched_del_{comp.get('id')}", use_container_width=True):
                    delete_competition(safe_str(comp.get("id")))
                    st.success("已刪除")
                    st.rerun()
        else:
            st.markdown(f"**{name}**")
            st.caption(detail)


def render_coach_competition_schedule() -> None:
    ensure_season_competition_schedule()
    st.markdown("#### 賽事時間表")
    st.caption("輸入比賽日期與名稱；學生平台「賽事時間表」會顯示賽事預告。")

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("比賽名稱", key="coach_sched_name", placeholder="例如：校際田徑賽")
    with c2:
        comp_date = st.date_input("比賽日期", value=date.today(), key="coach_sched_date")
    if st.button("加入賽事時間表", type="primary", use_container_width=True, key="coach_sched_add"):
        ok, msg = add_schedule_competition(name, comp_date)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("##### 即將舉行")
    upcoming = get_competition_schedule(upcoming_only=True, published_only=False)
    _render_schedule_list(upcoming, show_delete=True)

    past = [
        c for c in get_competitions(published_only=False)
        if safe_str(c.get("date")) < date.today().isoformat()
    ]
    if past:
        with st.expander(f"過往賽事（{len(past)}）", expanded=False):
            _render_schedule_list(list(reversed(past)), show_delete=True)


def render_student_competition_schedule() -> None:
    ensure_season_competition_schedule()
    st.markdown("#### 賽事時間表")
    st.markdown("##### 賽事預告")
    st.caption("教練公布的比賽日期，方便你知道幾時有比賽。")
    upcoming = get_competition_schedule(upcoming_only=True, published_only=True)
    _render_schedule_list(upcoming, show_delete=False)
