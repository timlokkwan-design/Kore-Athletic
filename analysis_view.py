"""V6 成效分析 — Foster 負荷 / ACWR / 配速一致性."""

from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from utils.acwr import acwr_status, calc_acwr
from utils.data_store import get_all_logs, get_student_names
from utils.helpers import parse_time


def render_analysis() -> None:
    from utils.auth import require_coach_or_stop
    require_coach_or_stop()
    st.subheader("📈 訓練負荷分析 (Foster 法)")
    st.caption("負荷 = 訓練時長(分) × RPE × 類型權重 | ACWR = 7日負荷 / 28日負荷")

    athletes = get_student_names()
    if not athletes:
        st.info("尚無選手資料")
        return

    c1, c2, c3 = st.columns(3)
    athlete = c1.selectbox("選擇選手", athletes)
    date_from = c2.date_input("起始", value=date.today() - timedelta(days=28))
    date_to = c3.date_input("結束", value=date.today())

    logs = get_all_logs()
    logs = logs[(logs["student_name"] == athlete) & (logs["date"].astype(str) >= date_from.isoformat()) &
                (logs["date"].astype(str) <= date_to.isoformat())]

    tab1, tab2, tab3 = st.tabs(["每週訓練負荷", "配速一致性", "ACWR 趨勢"])

    with tab1:
        if logs.empty:
            st.write("無數據")
        else:
            logs_copy = logs.copy()
            logs_copy["week"] = logs_copy["date"].astype(str).str[:7]
            weekly = logs_copy.groupby("week")["load"].sum().reset_index()
            fig = px.bar(weekly, x="week", y="load", title="每週訓練負荷")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        avgs = logs[logs["avg_pace"].notna() & (logs["avg_pace"] != "-")]["avg_pace"].astype(float).tolist() if not logs.empty else []
        if len(avgs) > 1:
            mean = sum(avgs) / len(avgs)
            std = (sum((v - mean) ** 2 for v in avgs) / len(avgs)) ** 0.5
            st.write(f"平均配速: **{mean:.2f}s**")
            st.write(f"標準差: **{std:.2f}s** {'✅ 穩定' if std < 2 else '⚠️ 波動大'}")
            st.write(f"樣本: {len(avgs)} 組")
        else:
            st.write("數據不足")

    with tab3:
        if logs.empty:
            st.write("無數據")
        else:
            dates = sorted(logs["date"].astype(str).unique())[-8:]
            acwr_data = [{"date": d, "acwr": calc_acwr(get_all_logs(), athlete, date.fromisoformat(d))} for d in dates]
            df = __import__("pandas").DataFrame(acwr_data)
            df["label"] = df["acwr"].apply(lambda v: acwr_status(v)[0])
            fig = px.bar(df, x="date", y="acwr", text="label", title="ACWR 趨勢")
            fig.add_hline(y=0.8, line_dash="dash", line_color="gray")
            fig.add_hline(y=1.3, line_dash="dash", line_color="orange")
            fig.add_hline(y=1.5, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
