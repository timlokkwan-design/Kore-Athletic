"""Student view — V6 all 4 sub-tabs."""

from datetime import date

import plotly.express as px
import streamlit as st

from utils.auth import refresh_current_user, require_student_or_stop
from utils.config import EVENTS
from utils.data_store import (
    get_program,
    get_wellness, get_attendance_record, load_attendance, mark_leave,
    submit_pending_record, submit_wellness, load_race_records, days_until_competition,
)
from utils.helpers import format_train_duration, needs_wind, parse_time, program_specs, safe_int, safe_str
from views.components.checkin import render_student_checkin_bar
from views.components.comp_registration import render_student_comp_registration
from views.components.mobile_nav import render_student_quick_dock
from views.components.schedule import render_student_schedule_calendar
from views.components.student_profile import render_student_profile
from views.components.student_training_log import render_student_training_log
from views.components.theme import render_page_header, render_stat_cards

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
    render_student_training_log(user)


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
    st.markdown("#### 📝 請假登記")
    st.caption("簽到請使用上方「立即簽到」；簽到後會記錄於「訓練時間表」月曆。")
    rec = get_attendance_record(name, date.today().isoformat())
    if rec and rec.get("status") == "present":
        dur = safe_int(rec.get("duration_minutes"), 0)
        msg = f"今日已簽到 {rec.get('detail', '')}"
        if dur > 0:
            msg += f" · 訓練 {format_train_duration(dur)}"
        st.success(msg)
    reason = st.selectbox("請假/缺席原因", ["", "病假", "學校活動", "家庭原因", "受傷", "其他"])
    if st.button("登記請假") and reason:
        mark_leave(name, reason)
        st.success("已登記請假")
        st.rerun()
    att = load_attendance()
    today = date.today().isoformat()
    row = att[(att["date"].astype(str) == today) & (att["athlete_name"] == name)] if not att.empty else att
    if row.empty:
        st.write("今日尚未簽到或請假")
    elif row.iloc[-1]["status"] == "leave":
        st.info(f"📝 請假：{row.iloc[-1]['detail']}")
