"""Student training log — record results, browse history, compare past schedules."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from utils.config import normalize_train_type
from utils.data_store import (
    append_training_log,
    get_logs_for_athlete,
    get_program,
    get_today_menu,
)
from utils.helpers import (
    app_today,
    format_time_venue_line,
    format_timetable_date,
    is_workout_content_unlocked,
    program_specs,
    safe_float,
    safe_int,
    safe_str,
    student_visible_program_specs,
    student_visible_workout_detail,
    workout_detail,
)
from views.components.theme import render_empty_state
from views.components.timer import render_lap_timer


def _log_dates_for_athlete(name: str) -> list[str]:
    logs = get_logs_for_athlete(name)
    if logs.empty:
        return []
    dates = sorted({str(d)[:10] for d in logs["date"].astype(str).tolist()}, reverse=True)
    return [d for d in dates if d]


def _logs_on_date(name: str, ds: str):
    logs = get_logs_for_athlete(name)
    if logs.empty:
        return logs
    return logs[logs["date"].astype(str).str[:10] == ds].sort_values("submitted_at", ascending=False)


def _render_program_card(prog: dict, *, title: str = "當日課表") -> None:
    day = safe_str(prog.get("date")) or None
    tp = normalize_train_type(safe_str(prog.get("type")))
    unlocked = is_workout_content_unlocked(day)
    specs = (student_visible_program_specs(prog, day) or tp or "—") if unlocked else (tp or "訓練")
    tv = format_time_venue_line(prog)
    detail = student_visible_workout_detail(prog, day)
    tips = safe_str(prog.get("tips")) if unlocked else ""
    st.markdown(f"**{title}** · {tp}")
    st.caption(specs)
    if tv:
        st.caption(f"🕐 {tv}")
    if detail:
        with st.expander("跑案內容", expanded=True):
            st.markdown(detail)
    elif day and not unlocked:
        st.info("跑案內容於訓練當日 **00:00（香港時間）** 開放。")
    if tips:
        st.caption(f"教練備註：{tips}")


def _render_log_card(row) -> None:
    ds = str(row.get("date", ""))[:10]
    event = safe_str(row.get("event")) or safe_str(row.get("train_type")) or "訓練"
    actual = safe_float(row.get("actual_seconds"))
    rpe = safe_int(row.get("rpe"), 0)
    duration = safe_int(row.get("duration"), 0)
    load = safe_int(row.get("load"), 0)
    laps = safe_str(row.get("laps_text"))
    remark = safe_str(row.get("remark"))
    submitted = safe_str(row.get("submitted_at"))
    st.markdown(
        f"**{format_timetable_date(ds)}** · {event}  \n"
        f"成績均速 **{actual:g}s** · RPE {rpe} · {duration} 分鐘 · 負荷 {load}"
    )
    if laps:
        st.caption(f"分組：{laps}")
    if remark:
        st.caption(f"備註：{remark}")
    if submitted:
        st.caption(f"提交於 {submitted}")


def _render_record_form(user: dict) -> None:
    specialty = user.get("specialty") or "短跑"
    today = app_today()
    log_date = st.date_input(
        "記錄日期",
        value=today,
        max_value=today,
        min_value=today - timedelta(days=60),
        key="stu_log_date",
        help="可補記近 60 日內的訓練成績",
    )
    prog = get_program(log_date, specialty=specialty)
    menu = get_today_menu(log_date, specialty=specialty)
    train_type = normalize_train_type(safe_str(prog.get("type"), "間歇跑"))
    day_key = log_date.isoformat() if hasattr(log_date, "isoformat") else str(log_date)[:10]
    summary = student_visible_program_specs(prog, day_key) or train_type

    st.info(f"**{format_timetable_date(day_key)}** 課表：{summary}")
    _render_program_card(prog, title="對照課表")

    existing = _logs_on_date(user["name"], log_date.isoformat())
    if not existing.empty:
        st.warning(f"此日已有 {len(existing)} 筆紀錄（仍可再提交補充）")

    lap_times: list[float] = []
    lap_reactions: list[str] = []
    if train_type in ("間歇跑", "節奏跑", "恢復跑"):
        if "n_lap_rows" not in st.session_state:
            st.session_state.n_lap_rows = 1
        n_laps = int(st.session_state.n_lap_rows)
        st.caption(f"共 {n_laps} 組")
        for i in range(n_laps):
            with st.container(border=True):
                st.markdown(f"**第 {i + 1} 組**")
                c1, c2 = st.columns(2)
                lap_times.append(
                    c1.number_input("時間(秒)", 0.0, 999.0, 0.0, step=0.1, key=f"lap_t_{i}")
                )
                lap_reactions.append(c2.text_input("身體反應", key=f"lap_r_{i}"))
        if st.button("＋ 新增一組", key="add_lap_row"):
            st.session_state.n_lap_rows = n_laps + 1
            st.rerun()
        if specialty == "短跑":
            st.number_input("反應時 (選填)", step=0.001, key="log_reaction")
        if specialty == "中長跑":
            st.number_input("最後 200m 衝刺時間", key="log_kick")
    elif specialty == "跨欄":
        st.number_input("欄間節奏(秒)", step=0.01, key="hurdle_rhythm")
        st.number_input("順欄數", 1, 20, 10, key="hurdle_count")
    elif train_type == "比賽" or specialty in ("田項", "田賽"):
        st.text_input("最佳試跳/投", key="field_best")
        st.number_input("試次數", 1, 20, 6, key="field_attempts")
    elif train_type == "肌力課":
        st.text_input("完成組數 x 次數", placeholder="深蹲 4x8", key="strength_note")
    elif train_type == "技術課":
        st.text_area("技術練習重點回報", key="tech_notes")
    else:
        st.caption("依當日課表類型填寫訓練成績。")

    rpe = st.slider("RPE 自覺強度 (1-10)", 1, 10, 5, key="stu_log_rpe")
    duration = st.number_input(
        "訓練時長 (分鐘)",
        1,
        300,
        int(prog.get("duration") or 60),
        key="stu_log_duration",
    )
    remark = st.text_area("總結備註", height=80, key="stu_log_remark")

    st.markdown("#### 分圈計時器")
    timer_laps = render_lap_timer()
    if timer_laps and train_type in ("間歇跑", "節奏跑", "恢復跑"):
        st.caption("計時器記圈結果可填入上方表單")

    if st.button("提交訓練成績", type="primary", use_container_width=True, key="stu_log_submit"):
        valid = [t for t in lap_times if t > 0]
        avg = sum(valid) / len(valid) if valid else 0.0
        laps_text = "、".join(f"{t}s({r})" for t, r in zip(lap_times, lap_reactions) if t > 0)
        extra: dict = {}
        if train_type in ("間歇跑", "節奏跑", "恢復跑") and specialty == "短跑":
            extra["reaction"] = st.session_state.get("log_reaction")
        if specialty == "中長跑":
            extra["kick"] = st.session_state.get("log_kick")
        if specialty == "跨欄":
            extra["hurdle_rhythm"] = st.session_state.get("hurdle_rhythm")
            extra["hurdle_count"] = st.session_state.get("hurdle_count")
        if train_type == "比賽" or specialty in ("田項", "田賽"):
            extra["field_best"] = st.session_state.get("field_best")
            extra["field_attempts"] = st.session_state.get("field_attempts")
        if train_type == "肌力課":
            extra["strength_note"] = st.session_state.get("strength_note")
        if train_type == "技術課":
            extra["tech_notes"] = st.session_state.get("tech_notes")
        append_training_log(
            student_name=user["name"],
            rep_number=1,
            actual_seconds=avg if avg else float(prog.get("target_seconds") or 0),
            rpe=rpe,
            injury_notes="無不適",
            menu=menu,
            duration=int(duration),
            remark=remark,
            laps_text=laps_text,
            avg_pace=f"{avg:.2f}" if avg else "-",
            **extra,
        )
        load = int(duration * rpe * 1.5)
        st.success(f"✅ 已記錄 {format_timetable_date(log_date.isoformat())} 成績！Foster 負荷: {load}")
        st.balloons()
        st.rerun()


def _render_history(user: dict) -> None:
    name = user["name"]
    specialty = user.get("specialty") or ""
    dates = _log_dates_for_athlete(name)
    if not dates:
        render_empty_state("尚無訓練紀錄", "提交第一筆訓練成績後會顯示於此")
        return

    st.caption(f"共 {len(dates)} 個有紀錄的日子")
    pick = st.selectbox(
        "選擇日期",
        dates,
        format_func=lambda d: format_timetable_date(d),
        key="stu_log_hist_date",
    )
    rows = _logs_on_date(name, pick)
    prog = get_program(date.fromisoformat(pick), specialty=specialty)

    left, right = st.columns(2)
    with left:
        st.markdown("##### 當日課表")
        _render_program_card(prog, title=format_timetable_date(pick))
    with right:
        st.markdown("##### 我的紀錄")
        for _, row in rows.iterrows():
            with st.container(border=True):
                _render_log_card(row)


def _recent_program_dates(specialty: str, *, days_back: int = 45) -> list[str]:
    """Dates in the past window that have a non-empty / non-rest program for this specialty."""
    today = app_today()
    out: list[str] = []
    for i in range(1, days_back + 1):
        d = today - timedelta(days=i)
        prog = get_program(d, specialty=specialty)
        tp = normalize_train_type(safe_str(prog.get("type")))
        if tp in ("休息", "待排課", ""):
            detail = workout_detail(prog)
            if not detail and not program_specs(prog):
                continue
        if tp == "休息":
            continue
        out.append(d.isoformat())
    return out


def _render_compare(user: dict) -> None:
    specialty = user.get("specialty") or "短跑"
    st.caption("揀兩日課表左右對照；亦可對照「課表 vs 當日成績」。")

    prog_dates = _recent_program_dates(specialty)
    log_dates = _log_dates_for_athlete(user["name"])
    choices = sorted(set(prog_dates) | set(log_dates), reverse=True)
    if not choices:
        render_empty_state("暫無可比較的課表", "教練排課或你提交紀錄後即可比較")
        return

    c1, c2 = st.columns(2)
    with c1:
        left_ds = st.selectbox(
            "左側日期",
            choices,
            index=0,
            format_func=format_timetable_date,
            key="stu_cmp_left",
        )
    with c2:
        right_default = 1 if len(choices) > 1 else 0
        right_ds = st.selectbox(
            "右側日期",
            choices,
            index=right_default,
            format_func=format_timetable_date,
            key="stu_cmp_right",
        )

    mode = st.radio(
        "比較內容",
        ["課表 vs 課表", "課表 vs 我的成績"],
        horizontal=True,
        key="stu_cmp_mode",
    )

    left_prog = get_program(date.fromisoformat(left_ds), specialty=specialty)
    right_prog = get_program(date.fromisoformat(right_ds), specialty=specialty)

    a, b = st.columns(2)
    with a:
        st.markdown(f"##### {format_timetable_date(left_ds)}")
        _render_program_card(left_prog, title="課表")
        left_logs = _logs_on_date(user["name"], left_ds)
        if not left_logs.empty and mode == "課表 vs 我的成績":
            st.markdown("**當日成績**")
            for _, row in left_logs.iterrows():
                with st.container(border=True):
                    _render_log_card(row)
    with b:
        st.markdown(f"##### {format_timetable_date(right_ds)}")
        if mode == "課表 vs 課表":
            _render_program_card(right_prog, title="課表")
        else:
            _render_program_card(right_prog, title="課表")
            right_logs = _logs_on_date(user["name"], right_ds)
            if right_logs.empty:
                st.info("此日尚未有你的訓練成績")
            else:
                st.markdown("**當日成績**")
                for _, row in right_logs.iterrows():
                    with st.container(border=True):
                        _render_log_card(row)


def render_student_training_log(user: dict) -> None:
    st.markdown("#### 訓練日誌")
    tab = st.radio(
        "功能",
        ["記錄成績", "過往紀錄", "課表比較"],
        horizontal=True,
        key="stu_log_main_tab",
        label_visibility="collapsed",
    )
    if tab == "記錄成績":
        _render_record_form(user)
    elif tab == "過往紀錄":
        _render_history(user)
    else:
        _render_compare(user)
