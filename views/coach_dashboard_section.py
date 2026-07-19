"""Coach dashboard — at-a-glance overview."""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import streamlit as st

from utils.acwr import calc_acwr, needs_rest
from utils.coach_pending import get_coach_pending_summary
from utils.config import GROUP_OPTIONS, SPECIALTY_TO_GROUP, group_display_label, normalize_group
from utils.data_store import (
    get_all_logs,
    get_attendance_today,
    get_students,
    get_wellness,
)
from utils.helpers import safe_str
from views.components.coach_pending_alert import navigate_to_coach_pending
from views.components.theme import render_stat_cards

_GROUP_ORDER = [group_display_label(g) for g in GROUP_OPTIONS if g != "全體組員"] + ["未分類"]


def _group_label_for_student(student: dict) -> str:
    specialty = safe_str(student.get("specialty"))
    mapped = SPECIALTY_TO_GROUP.get(specialty, "")
    if mapped:
        return group_display_label(normalize_group(mapped))
    return specialty or "未分類"


def _render_absent_by_group(students: list[dict], att) -> None:
    """List students not checked in today, grouped by training group."""
    missing_by_group: dict[str, list[str]] = defaultdict(list)
    for student in students:
        name = safe_str(student.get("name"))
        if not name:
            continue
        if att.empty or att[att["athlete_name"].astype(str) == name].empty:
            missing_by_group[_group_label_for_student(student)].append(name)

    if not missing_by_group:
        return

    st.markdown("##### ❌ 今日尚未簽到")
    total = sum(len(v) for v in missing_by_group.values())
    st.caption(f"共 {total} 人 · 已按組別分類")

    ordered = [g for g in _GROUP_ORDER if g in missing_by_group]
    ordered += sorted(g for g in missing_by_group if g not in _GROUP_ORDER)

    for group_label in ordered:
        names = missing_by_group[group_label]
        with st.expander(f"👥 {group_label}（{len(names)}）", expanded=True):
            st.write("、".join(names))


def render_coach_dashboard() -> None:
    st.markdown("#### 今日總覽")
    students = get_students()
    if not students:
        from views.components.theme import render_empty_state

        render_empty_state("尚無已核准學員", "請至「隊伍管理 → 待審事項」核准新學員")
        return
    student_names = [safe_str(s.get("name")) for s in students]
    att = get_attendance_today()
    logs = get_all_logs()

    present = 0
    leave = 0
    absent = 0
    for name in student_names:
        if att.empty:
            absent += 1
            continue
        row = att[att["athlete_name"].astype(str) == name]
        if row.empty:
            absent += 1
        elif safe_str(row.iloc[-1].get("status")) == "present":
            present += 1
        else:
            leave += 1

    acwr_alerts = 0
    for name in student_names:
        acwr = calc_acwr(logs, name)
        wellness = get_wellness(athlete=name)
        if needs_rest(acwr, wellness):
            acwr_alerts += 1

    pending = get_coach_pending_summary()
    pending_users = pending["registrations"]
    pending_scores = pending["scores"]
    pending_spec = pending["specialty"]

    render_stat_cards([
        ("已核准學員", str(len(students)), "normal"),
        ("今日出席", str(present), "success"),
        ("今日請假", str(leave), "warn" if leave else "normal"),
        ("尚未簽到", str(absent), "danger" if absent else "normal"),
        ("ACWR 警示", str(acwr_alerts), "danger" if acwr_alerts else "success"),
        ("待審註冊", str(pending_users), "warn" if pending_users else "normal"),
        ("待審成績", str(pending_scores), "warn" if pending_scores else "normal"),
        ("待審專項", str(pending_spec), "warn" if pending_spec else "normal"),
    ])

    st.caption(f"更新日期：{date.today().isoformat()} · 詳細資料請使用左側子選單。")

    if pending_users or pending_scores or pending_spec:
        st.markdown("##### ⏳ 待處理事項")
        if pending_users:
            st.info(f"有 **{pending_users}** 位新學員待核准")
        if pending_scores:
            st.info(f"有 **{pending_scores}** 筆比賽成績待審")
        if pending_spec:
            st.info(f"有 **{pending_spec}** 項專項更改待審")
        if st.button("前往待審事項", key="dashboard_go_pending", type="primary"):
            navigate_to_coach_pending()
            st.rerun()

    if absent:
        _render_absent_by_group(students, att)
