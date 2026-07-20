"""Coach attendance sheet — today / week / month views."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from utils.config import GROUP_OPTIONS, SPECIALTY_TO_GROUP, group_display_label, normalize_group
from utils.data_store import (
    attendance_rate,
    attendance_status_symbol,
    build_coach_attendance_log,
    build_coach_attendance_matrix,
    get_attendance_for_week,
    get_attendance_today,
    get_students,
    get_week_range,
)
from utils.helpers import safe_str
from views.components.avatar import athlete_card_html, render_person
from views.components.theme import render_stat_cards

_FILTER_ALL = "全部組別"
_GROUP_FILTERS = [_FILTER_ALL] + [
    group_display_label(g) for g in GROUP_OPTIONS if g != "全體組員"
]


def _group_label_for_student(student: dict) -> str:
    specialty = safe_str(student.get("specialty"))
    mapped = SPECIALTY_TO_GROUP.get(specialty, "")
    if mapped:
        return group_display_label(normalize_group(mapped))
    return specialty or "未分類"


def _filter_students_by_group(students: list[dict], group_label: str) -> list[dict]:
    if group_label == _FILTER_ALL:
        return students
    return [s for s in students if _group_label_for_student(s) == group_label]


def _status_label(status: str, detail: str) -> str:
    if status == "present":
        return f"✅ 出席 {detail}".strip()
    if status == "leave":
        return f"📝 請假 {detail}".strip()
    return "❌ 缺席"


def _lookup_attendance(att_df, name: str, day: str) -> dict | None:
    if att_df.empty:
        return None
    rows = att_df[
        (att_df["athlete_name"].astype(str) == name)
        & (att_df["date"].astype(str).str[:10] == day)
    ]
    if rows.empty:
        return None
    row = rows.iloc[-1]
    return {
        "status": safe_str(row.get("status")),
        "detail": safe_str(row.get("detail")),
        "duration_minutes": row.get("duration_minutes"),
    }


def _today_status_rank(student: dict, att_today) -> int:
    """Sort key: unsigned (0) → leave (1) → present (2)."""
    name = safe_str(student.get("name"))
    row = _lookup_attendance(att_today, name, date.today().isoformat())
    if not row:
        return 0
    if row["status"] == "leave":
        return 1
    if row["status"] == "present":
        return 2
    return 0


def _render_today_summary(students: list[dict], att_today) -> None:
    present = leave = absent = 0
    for student in students:
        name = safe_str(student.get("name"))
        row = _lookup_attendance(att_today, name, date.today().isoformat())
        if not row:
            absent += 1
        elif row["status"] == "present":
            present += 1
        else:
            leave += 1
    render_stat_cards([
        ("學員", str(len(students)), "normal"),
        ("今日出席", str(present), "success"),
        ("今日請假", str(leave), "warn" if leave else "normal"),
        ("尚未簽到", str(absent), "danger" if absent else "normal"),
    ])


def _render_student_card(student: dict, att_today) -> None:
    name = safe_str(student.get("name"))
    specialty = safe_str(student.get("specialty"))
    row = _lookup_attendance(att_today, name, date.today().isoformat())
    status_text = "❌ 尚未簽到"
    if row:
        status_text = _status_label(row["status"], row["detail"])
    from views.components.theme import get_ui_colors

    uc = get_ui_colors()
    st.markdown(
        athlete_card_html(
            name,
            f"<div style='font-size:0.9rem;color:{uc['muted']};'>{specialty}<br>{status_text}</div>",
            username=safe_str(student.get("username")),
            bg=uc["card_bg"],
        ),
        unsafe_allow_html=True,
    )


def _render_today_cards(students: list[dict], att_today) -> None:
    ordered = sorted(students, key=lambda s: (_today_status_rank(s, att_today), safe_str(s.get("name"))))
    pending = [s for s in ordered if _today_status_rank(s, att_today) < 2]
    present = [s for s in ordered if _today_status_rank(s, att_today) == 2]

    for student in pending:
        _render_student_card(student, att_today)

    if present:
        with st.expander(f"✅ 已簽到（{len(present)}）", expanded=False):
            for student in present:
                _render_student_card(student, att_today)


def _render_week_view(students: list[dict]) -> None:
    start, end = get_week_range()
    st.caption(f"本週：{start.isoformat()} 至 {end.isoformat()}（一至日）")
    att_week = get_attendance_for_week()
    day_cols = ["一", "二", "三", "四", "五", "六", "日"]
    days = [(start + timedelta(days=i)).isoformat() for i in range(7)]

    for student in students:
        name = safe_str(student.get("name"))
        cells = []
        for d, label in zip(days, day_cols):
            rec = _lookup_attendance(att_week, name, d)
            if not rec:
                cells.append(f"{label} —")
            else:
                sym = attendance_status_symbol(rec["status"])
                cells.append(f"{label} {sym}")
        week_line = " · ".join(cells)
        render_person(
            name,
            subtitle=week_line,
            username=safe_str(student.get("username")),
            size=36,
        )


def _render_month_view(students: list[dict], year: int, month: int) -> None:
    st.markdown("##### 出席率（本月累計）")
    for student in students:
        name = safe_str(student.get("name"))
        render_person(
            name,
            subtitle=f"出席率 {attendance_rate(name)}%",
            username=safe_str(student.get("username")),
            size=36,
        )

    st.markdown("##### 出席明細")
    log_df = build_coach_attendance_log(year, month)
    if log_df.empty:
        st.caption("本月尚無出席明細")
    else:
        names = {safe_str(s.get("name")) for s in students}
        for _, row in log_df.iterrows():
            if safe_str(row.get("姓名")) not in names:
                continue
            st.markdown(
                f"**{row.get('姓名', '—')}** · "
                f"{row.get('日期', '—')} · {row.get('狀態', '—')} · {row.get('詳情', '')}"
            )

    with st.expander("月曆矩陣表（完整欄位 · 闊螢幕適用）", expanded=False):
        st.caption("✅ 出席 · 📝 請假 · — 無紀錄 · 數字為訓練分鐘")
        matrix = build_coach_attendance_matrix(year, month)
        if matrix.empty:
            st.write("本月尚無出席紀錄")
        else:
            st.dataframe(matrix, use_container_width=True, hide_index=True)


def render_coach_attendance() -> None:
    st.subheader("學生出席表")
    students = get_students()
    if not students:
        st.info("尚無已核准學員，請先在「隊伍管理 → 待審事項」核准註冊。")
        return

    today = date.today()
    if "coach_att_year" not in st.session_state:
        st.session_state.coach_att_year = today.year
        st.session_state.coach_att_month = today.month

    year = st.session_state.coach_att_year
    month = st.session_state.coach_att_month

    from views.components.coach_mobile_ui import render_option_chips

    group_label = render_option_chips(
        key="coach_att_group_chips",
        options=_GROUP_FILTERS,
        session_key="coach_att_group",
        caption="組別篩選",
        per_row=4,
    )
    students = _filter_students_by_group(students, group_label)
    if not students:
        st.info("此組別暫無學員。")
        return

    view = st.radio(
        "檢視",
        ["今日", "本週", "本月"],
        horizontal=True,
        key="coach_att_view_mode",
    )

    att_today = get_attendance_today()

    if view == "今日":
        _render_today_summary(students, att_today)
        st.markdown("##### 學員狀態")
        _render_today_cards(students, att_today)
        return

    if view == "本週":
        _render_week_view(students)
        return

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 上月", key="coach_att_prev"):
        if month == 1:
            st.session_state.coach_att_month, st.session_state.coach_att_year = 12, year - 1
        else:
            st.session_state.coach_att_month -= 1
        st.rerun()
    c2.markdown(f"### {year} 年 {month:02d} 月")
    if c3.button("下月 ▶", key="coach_att_next"):
        if month == 12:
            st.session_state.coach_att_month, st.session_state.coach_att_year = 1, year + 1
        else:
            st.session_state.coach_att_month += 1
        st.rerun()

    _render_month_view(students, year, month)
