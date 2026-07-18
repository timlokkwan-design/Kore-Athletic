"""Coach-facing dashboard with student overview and charts."""

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_store import get_all_logs, get_today_menu


def render_coach_view() -> None:
    st.title("🎯 教練端")
    st.caption("查看所有學生訓練數據與目標達成狀況")

    menu = get_today_menu()
    logs = get_all_logs()

    _render_menu_summary(menu)
    st.divider()

    if logs.empty:
        st.warning("目前尚無學生訓練數據。請先在學生端提交記錄。")
        return

    date_filter = st.date_input("篩選日期", value=date.today())
    filtered = logs[logs["date"].astype(str) == date_filter.isoformat()].copy()

    if filtered.empty:
        st.info(f"{date_filter.isoformat()} 沒有訓練記錄。")
        return

    _render_overview_metrics(filtered)
    st.divider()
    _render_comparison_charts(filtered)
    st.divider()
    _render_full_table(filtered)


def _render_menu_summary(menu: dict) -> None:
    st.subheader("📋 今日訓練設定")
    st.write(
        f"**{menu['date']}** · {menu['description']} · "
        f"目標 **{menu['target_seconds']:.1f}** 秒"
    )


def _render_overview_metrics(logs: pd.DataFrame) -> None:
    st.subheader("📈 數據總覽")

    student_count = logs["student_name"].nunique()
    rep_count = len(logs)
    avg_delta = (logs["actual_seconds"] - logs["target_seconds"]).mean()
    injury_count = len(logs[~logs["injury_notes"].isin(["無不適", "", None])])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("學生人數", student_count)
    c2.metric("總記錄趟數", rep_count)
    c3.metric("平均差距", f"{avg_delta:+.1f} 秒", help="實際秒數 − 目標秒數")
    c4.metric("有不適回報", injury_count)


def _render_comparison_charts(logs: pd.DataFrame) -> None:
    st.subheader("📊 目標 vs 實際秒數")

    tab1, tab2, tab3 = st.tabs(["依學生平均", "依趟數", "RPE 分布"])

    with tab1:
        avg_by_student = (
            logs.groupby("student_name", as_index=False)
            .agg(target_seconds=("target_seconds", "mean"), actual_seconds=("actual_seconds", "mean"))
        )
        avg_by_student["label"] = avg_by_student["student_name"]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="目標秒數",
                x=avg_by_student["label"],
                y=avg_by_student["target_seconds"],
                marker_color="#4C78A8",
            )
        )
        fig.add_trace(
            go.Bar(
                name="實際秒數",
                x=avg_by_student["label"],
                y=avg_by_student["actual_seconds"],
                marker_color="#F58518",
            )
        )
        fig.update_layout(
            barmode="group",
            xaxis_title="學生",
            yaxis_title="秒數",
            legend_title="",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        logs_sorted = logs.sort_values(["student_name", "rep_number"])
        logs_sorted["趟次標籤"] = logs_sorted.apply(
            lambda r: f"{r['student_name']}-第{r['rep_number']}趟", axis=1
        )

        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=logs_sorted["趟次標籤"],
                y=logs_sorted["target_seconds"],
                mode="lines+markers",
                name="目標秒數",
                line=dict(color="#4C78A8", dash="dash"),
            )
        )
        fig2.add_trace(
            go.Scatter(
                x=logs_sorted["趟次標籤"],
                y=logs_sorted["actual_seconds"],
                mode="lines+markers",
                name="實際秒數",
                line=dict(color="#F58518"),
            )
        )
        fig2.update_layout(
            xaxis_title="趟次",
            yaxis_title="秒數",
            legend_title="",
            height=400,
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        fig3 = px.histogram(
            logs,
            x="rpe",
            color="student_name",
            barmode="group",
            nbins=10,
            title="RPE 自覺強度分布",
            labels={"rpe": "RPE", "student_name": "學生"},
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)


def _render_full_table(logs: pd.DataFrame) -> None:
    st.subheader("📝 完整記錄表")

    display = logs[
        [
            "student_name",
            "rep_number",
            "target_seconds",
            "actual_seconds",
            "rpe",
            "injury_notes",
            "submitted_at",
        ]
    ].copy()
    display["差距"] = display["actual_seconds"] - display["target_seconds"]
    display = display.sort_values(["student_name", "rep_number"])

    display.columns = ["姓名", "趟數", "目標秒數", "實際秒數", "RPE", "不適部位", "提交時間", "差距"]
    display["目標秒數"] = display["目標秒數"].map(lambda x: f"{x:.1f}")
    display["實際秒數"] = display["實際秒數"].map(lambda x: f"{x:.1f}")
    display["差距"] = display["差距"].map(lambda x: f"{x:+.1f}")

    st.dataframe(display, use_container_width=True, hide_index=True)

    injury_rows = logs[~logs["injury_notes"].isin(["無不適", "", None])]
    if not injury_rows.empty:
        st.warning("以下學生回報有不適，請留意：")
        for _, row in injury_rows.iterrows():
            st.write(f"- **{row['student_name']}**（第 {row['rep_number']} 趟）：{row['injury_notes']}")
