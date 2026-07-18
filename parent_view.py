"""V6 家長唯讀專區."""

import streamlit as st

from utils.acwr import acwr_status, calc_acwr
from utils.data_store import (
    get_all_logs, get_logs_for_athlete, get_program, get_wellness,
    load_periodization, load_race_records,
)
from utils.helpers import weekly_summary_text
from views.components.avatar import render_person
from views.components.board import render_training_board
from views.components.theme import render_page_header


def render_parent_view() -> None:
    from utils.auth import require_parent_or_stop
    user = require_parent_or_stop()
    child = user.get("child_name") or ""
    if not child:
        st.warning("帳號未連結子女資料，請聯絡教練。")
        st.stop()

    render_page_header("家長專區", f"子女：{child}")
    render_person(child, subtitle="訓練摘要", size=48)
    st.markdown(
        """<div style="background:#dcfce7;border:1px solid #86efac;padding:1rem;border-radius:8px;">
        <b>🔒 家長唯讀專區</b><br>
        <small>您可查看子女訓練摘要、出席率及 PB 進度，無法修改資料。</small></div>""",
        unsafe_allow_html=True,
    )

    render_training_board(show_specs=True)
    st.divider()

    logs = get_all_logs()
    child_logs = get_logs_for_athlete(child)
    att = __import__("utils.data_store", fromlist=["load_attendance"]).load_attendance()
    att_sub = att[att["athlete_name"] == child] if not att.empty else att
    pbs = load_race_records()
    pbs_sub = pbs[pbs["athlete_name"] == child] if not pbs.empty else pbs
    acwr = calc_acwr(logs, child)
    per = load_periodization()

    summary = weekly_summary_text(child, child_logs, att_sub, pbs_sub, acwr, per)
    st.subheader("📋 每週訓練摘要")
    st.text_area("摘要", summary, height=280, disabled=True, label_visibility="collapsed")

    st.subheader("🏆 子女 PB")
    if pbs_sub.empty:
        st.write("尚無成績")
    else:
        cols = st.columns(2)
        for i, (_, p) in enumerate(pbs_sub.head(6).iterrows()):
            with cols[i % 2]:
                st.markdown(f"**{p['item']}** · `{p['score']}` · {p['date']}")

    wellness = get_wellness(athlete=child)
    if wellness:
        st.subheader("💤 今日健康")
        st.write(f"睡眠 {wellness['sleep']}/5 · 酸痛 {wellness['soreness']}/5 · 心情 {wellness['mood']}/5")
        if wellness.get("sick"):
            st.warning("子女今日回報身體不適")

    label, _ = acwr_status(acwr)
    st.metric("ACWR", label)
