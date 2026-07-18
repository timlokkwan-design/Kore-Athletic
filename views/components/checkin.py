"""Prominent student check-in bar."""
from __future__ import annotations

from datetime import date

import streamlit as st

from utils.data_store import check_in, get_attendance_record, get_program
from utils.helpers import format_train_duration, safe_int, safe_str


def _duration_from_times(prog: dict) -> int:
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    if not start or not end or ":" not in start or ":" not in end:
        return 0
    try:
        sh, sm = (int(x) for x in start.split(":")[:2])
        eh, em = (int(x) for x in end.split(":")[:2])
        return max(0, (eh * 60 + em) - (sh * 60 + sm))
    except (TypeError, ValueError):
        return 0


def _default_duration_minutes(specialty: str = "") -> int:
    prog = get_program(specialty=specialty or None)
    dur = safe_int(prog.get("duration"), 0)
    if dur < 15:
        dur = _duration_from_times(prog)
    if dur < 15:
        dur = 60
    return min(dur, 300)


def render_student_checkin_bar(name: str, *, specialty: str = "", compact_when_done: bool = True) -> None:
    today = date.today().isoformat()
    rec = get_attendance_record(name, today)

    if rec and rec.get("status") == "present":
        dur = safe_int(rec.get("duration_minutes"), 0)
        time_str = rec.get("detail") or ""
        msg = f"✅ 今日已簽到 {time_str}"
        if dur > 0:
            msg += f" · 訓練 {format_train_duration(dur)}"
        if compact_when_done:
            from views.components.theme import render_compact_bar

            render_compact_bar(msg, tone="success")
            return
        with st.container(border=True):
            st.markdown("#### ✅ 訓練簽到")
            st.success(msg)
            st.caption("簽到記錄會顯示於「訓練時間表」月曆。")
        return

    with st.expander("✅ 訓練簽到 — 尚未簽到", expanded=True):
        default_dur = _default_duration_minutes(specialty)
        if st.session_state.get("student_checkin_duration", default_dur) < 15:
            st.session_state.student_checkin_duration = default_dur
        c1, c2 = st.columns([2, 1])
        with c1:
            duration = st.number_input(
                "訓練時長（分鐘）",
                min_value=15,
                max_value=300,
                value=default_dur,
                step=15,
                key="student_checkin_duration",
            )
        with c2:
            st.write("")
            st.write("")
            if st.button("一鍵簽到", type="primary", use_container_width=True, key="student_checkin_btn"):
                check_in(name, duration_minutes=int(duration))
                st.rerun()
