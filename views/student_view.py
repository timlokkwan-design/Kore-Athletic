"""Student view — V6 all 4 sub-tabs."""

from datetime import date

import plotly.express as px
import streamlit as st

from utils.auth import refresh_current_user, require_student_or_stop
from utils.config import EVENTS
from utils.data_store import (
    append_training_log, get_program,
    get_today_menu, get_wellness, get_attendance_record, load_attendance, mark_leave,
    submit_pending_record, submit_wellness, load_race_records, days_until_competition,
)
from utils.helpers import format_train_duration, needs_wind, parse_time, program_specs, safe_int, safe_str
from views.components.checkin import render_student_checkin_bar
from views.components.comp_registration import render_student_comp_registration
from views.components.mobile_nav import render_student_quick_dock
from views.components.schedule import render_student_schedule_calendar
from views.components.student_profile import render_student_profile
from views.components.theme import render_page_header, render_stat_cards
from views.components.timer import render_lap_timer

STUDENT_NAV_CATEGORIES: list[tuple[str, list[str]]] = [
    ("📅 每日訓練", ["訓練時間表", "訓練日誌", "健康問卷", "出席"]),
    ("🏅 比賽", ["比賽報名", "提交比賽成績"]),
    ("👤 帳戶", ["個人資料"]),
]

STUDENT_SECTIONS = [item for _, items in STUDENT_NAV_CATEGORIES for item in items]


def render_student_view(section: str) -> None:
    require_student_or_stop()
    user = refresh_current_user()
    specialty = user.get("specialty") or "—"
    render_page_header(
        "學生平台",
        f"{user['name']} · 專項：{specialty}",
    )
    render_student_quick_dock(section)
    render_student_checkin_bar(user["name"], specialty=user.get("specialty", ""))
    st.divider()

    if section == "訓練時間表":
        _tab_schedule(user)
    elif section == "個人資料":
        render_student_profile(user)
    elif section == "訓練日誌":
        _tab_training_log(user)
    elif section == "健康問卷":
        _tab_wellness(user["name"])
    elif section == "比賽報名":
        render_student_comp_registration(user)
    elif section == "提交比賽成績":
        _tab_pb(user["name"])
    elif section == "出席":
        _tab_attendance(user["name"])
    else:
        _tab_schedule(user)


def _tab_schedule(user: dict) -> None:
    specialty = user.get("specialty") or ""
    prog = get_program(specialty=specialty)
    today = date.today().isoformat()
    att = get_attendance_record(user["name"], today)
    checked_in = att and att.get("status") == "present"
    countdown = days_until_competition()

    checkin_label = "已簽到" if checked_in else "未簽到"
    checkin_tone = "success" if checked_in else "warn"
    countdown_label = f"{countdown} 天" if countdown is not None else "—"

    render_stat_cards([
        ("今日課表", program_specs(prog)[:12] or safe_str(prog.get("type"), "—")[:12], "normal"),
        ("簽到", checkin_label, checkin_tone),
        ("距離比賽", countdown_label, "normal"),
    ])

    st.markdown("#### 訓練時間表")
    st.caption(f"專項：**{user.get('specialty', '—')}**")
    render_student_schedule_calendar(user.get("specialty", ""), user["name"])


def _tab_training_log(user: dict) -> None:
    specialty = user.get("specialty") or "短跑"
    prog = get_program(specialty=specialty)
    menu = get_today_menu(specialty=specialty)
    train_type = prog.get("type", "間歇跑")

    st.markdown("#### 回傳今日訓練數據")
    st.info(f"今日課表：**{program_specs(prog) or prog.get('type')}** · 專項：**{specialty}**")

    lap_times, lap_reactions = [], []
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
        st.caption("依今日課表類型填寫。")

    rpe = st.slider("RPE 自覺強度 (1-10)", 1, 10, 5)
    duration = st.number_input("訓練時長 (分鐘) — Foster 負荷", 1, 300, int(prog.get("duration") or 60))
    remark = st.text_area("總結備註", height=80)

    st.markdown("#### 分圈計時器")
    timer_laps = render_lap_timer()
    if timer_laps and train_type in ("間歇跑", "節奏跑", "恢復跑"):
        st.caption("計時器記圈結果可填入上方表單")

    if st.button("提交訓練數據", type="primary", use_container_width=True):
        valid = [t for t in lap_times if t > 0]
        avg = sum(valid) / len(valid) if valid else 0
        laps_text = "、".join(f"{t}s({r})" for t, r in zip(lap_times, lap_reactions) if t > 0)
        extra = {}
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
            student_name=user["name"], rep_number=1,
            actual_seconds=avg if avg else float(prog.get("target_seconds") or 0),
            rpe=rpe, injury_notes="無不適", menu=menu, duration=int(duration), remark=remark,
            laps_text=laps_text, avg_pace=f"{avg:.2f}" if avg else "-", **extra,
        )
        load = int(duration * rpe * 1.5)
        st.success(f"✅ 提交成功！Foster 負荷: {load} (時長×RPE×類型權重)")
        st.balloons()


def _tab_wellness(name: str) -> None:
    st.markdown("#### 🛏️ 每日健康問卷")
    existing = get_wellness(athlete=name)
    sleep = st.slider("睡眠品質 (1-5)", 1, 5, existing["sleep"] if existing else 3)
    soreness = st.slider("肌肉酸痛 (1-5)", 1, 5, existing["soreness"] if existing else 2)
    mood = st.slider("心情 (1-5)", 1, 5, existing["mood"] if existing else 4)
    sick = st.checkbox("今日身體不適/生病", value=existing["sick"] if existing else False)
    if st.button("提交健康問卷", type="primary"):
        submit_wellness(name, sleep, soreness, mood, sick)
        st.success("已提交"); st.rerun()


def _tab_pb(name: str) -> None:
    st.markdown("#### 🏁 提交比賽成績")
    item = st.selectbox("項目", EVENTS, key="pb_item")
    score = st.text_input("成績", key="pb_score")
    comp_date = st.date_input("比賽日期", value=date.today(), key="pb_date")
    if needs_wind(item):
        wind = st.number_input("風速 m/s", step=0.1, key="pb_wind")
    else:
        wind = 0.0
        st.caption("此項目無需填寫風速")
    comp = st.text_input("比賽名稱", key="pb_comp")
    if st.button("提交待教練審核", type="primary", key="pb_submit"):
        submit_pending_record({
            "athlete_name": name, "item": item, "score": score,
            "wind": wind, "comp_name": comp, "date": comp_date.isoformat(),
        })
        st.success("已提交，待教練審核")

    st.markdown("#### 📈 個人 PB 進步曲線")
    chart_event = st.selectbox("項目", EVENTS, key="pb_chart")
    records = load_race_records()
    recs = records[(records["athlete_name"] == name) & (records["item"] == chart_event)] if not records.empty else records
    if recs.empty or len(recs) < 2:
        st.write("需要至少 2 筆紀錄")
    else:
        recs = recs.sort_values("date")
        recs["time_val"] = recs["score"].apply(parse_time)
        fig = px.line(recs, x="date", y="time_val", markers=True, title=f"{chart_event} 進步曲線")
        fig.update_layout(yaxis_title="秒數", height=350)
        st.plotly_chart(fig, use_container_width=True)


def _tab_attendance(name: str) -> None:
    from datetime import timedelta

    st.markdown("#### 📝 請假登記")
    st.caption("可預早為未來訓練日請假。簽到請用上方「立即簽到」。")
    today = date.today()
    leave_date = st.date_input(
        "請假日期",
        value=today,
        min_value=today,
        max_value=today + timedelta(days=60),
        format="YYYY/MM/DD",
        key="leave_date",
    )
    leave_key = leave_date.isoformat()
    rec = get_attendance_record(name, leave_key)
    if rec and rec.get("status") == "present":
        dur = safe_int(rec.get("duration_minutes"), 0)
        msg = f"{leave_key} 已簽到 {rec.get('detail', '')}"
        if dur > 0:
            msg += f" · 訓練 {format_train_duration(dur)}"
        st.success(msg)
    elif rec and rec.get("status") == "leave":
        st.info(f"📝 {leave_key} 已請假：{rec.get('detail', '')}")
    reason = st.selectbox(
        "請假/缺席原因",
        ["", "病假", "學校活動", "家庭原因", "受傷", "其他"],
        key="leave_reason",
    )
    if st.button("登記請假", type="primary", key="leave_submit") and reason:
        try:
            marked = mark_leave(name, reason, for_date=leave_date)
            st.success(f"已登記請假（{marked}）")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    att = load_attendance()
    if att.empty:
        return
    upcoming = att[
        (att["athlete_name"] == name)
        & (att["status"].astype(str) == "leave")
        & (att["date"].astype(str).str[:10] >= today.isoformat())
    ].sort_values("date")
    if not upcoming.empty:
        st.markdown("##### 已登記的請假")
        for _, row in upcoming.iterrows():
            st.write(f"📝 {str(row['date'])[:10]} · {row['detail']}")
