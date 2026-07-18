"""Student-facing training log interface."""

import streamlit as st

from utils.config import INJURY_OPTIONS
from utils.data_store import append_training_log, get_logs_for_date, get_today_menu


def render_student_view() -> None:
    st.title("🏃 學生端")
    st.caption("查看今日訓練菜單並記錄每趟成績")

    menu = get_today_menu()
    _render_today_menu(menu)
    st.divider()
    _render_submission_form(menu)
    st.divider()
    _render_my_records()


def _render_today_menu(menu: dict) -> None:
    st.subheader("📋 今日訓練菜單")
    col1, col2, col3 = st.columns(3)
    col1.metric("項目", menu["event"])
    col2.metric("趟數", f"{menu['reps']} 趟")
    col3.metric("目標秒數", f"{menu['target_seconds']:.1f} 秒")

    st.info(f"**{menu['description']}**")
    if menu.get("notes"):
        st.write(f"教練備註：{menu['notes']}")


def _render_submission_form(menu: dict) -> None:
    st.subheader("✍️ 記錄訓練數據")

    with st.form("training_log_form", clear_on_submit=True):
        student_name = st.text_input("姓名", placeholder="請輸入你的姓名")
        rep_number = st.number_input(
            "第幾趟",
            min_value=1,
            max_value=int(menu["reps"]),
            value=1,
            step=1,
        )
        actual_seconds = st.number_input(
            "實際秒數",
            min_value=0.0,
            max_value=999.0,
            value=float(menu["target_seconds"]),
            step=0.1,
            format="%.1f",
        )
        rpe = st.slider(
            "RPE 自覺強度",
            min_value=1,
            max_value=10,
            value=5,
            help="1 = 非常輕鬆，10 = 極度疲勞",
        )
        injury_notes = st.selectbox("傷病 / 不適部位", options=INJURY_OPTIONS)
        other_injury = st.text_input("其他不適說明（選填）", placeholder="若選「其他」請在此說明")

        submitted = st.form_submit_button("提交記錄", type="primary", use_container_width=True)

    if submitted:
        if not student_name.strip():
            st.error("請輸入姓名後再提交。")
            return

        notes = injury_notes
        if injury_notes == "其他" and other_injury.strip():
            notes = f"其他：{other_injury.strip()}"

        append_training_log(
            student_name=student_name,
            rep_number=int(rep_number),
            actual_seconds=float(actual_seconds),
            rpe=int(rpe),
            injury_notes=notes,
            menu=menu,
        )
        st.success(f"已記錄 {student_name} 第 {rep_number} 趟的數據！")
        st.balloons()


def _render_my_records() -> None:
    st.subheader("📊 我的今日記錄")

    name_filter = st.text_input("篩選姓名（選填）", key="student_name_filter")
    logs = get_logs_for_date()

    if name_filter.strip():
        logs = logs[logs["student_name"] == name_filter.strip()]

    if logs.empty:
        st.write("尚無記錄。提交第一筆數據後會顯示在這裡。")
        return

    display = logs[
        ["student_name", "rep_number", "target_seconds", "actual_seconds", "rpe", "injury_notes"]
    ].copy()
    display.columns = ["姓名", "趟數", "目標秒數", "實際秒數", "RPE", "不適部位"]
    display["目標秒數"] = display["目標秒數"].map(lambda x: f"{x:.1f}")
    display["實際秒數"] = display["實際秒數"].map(lambda x: f"{x:.1f}")

    st.dataframe(display, use_container_width=True, hide_index=True)
