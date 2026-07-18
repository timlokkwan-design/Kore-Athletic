"""PB leaderboard — by gender and event, anonymous scores only."""
from __future__ import annotations

import streamlit as st

from utils.config import EVENTS, GENDER_OPTIONS
from utils.data_store import get_pb_leaderboard_by_gender
from views.components.theme import render_empty_state, render_page_header


def _top_card_class(rank: int) -> str:
    if rank == 1:
        return "ka-lb-top1"
    if rank == 2:
        return "ka-lb-top2"
    if rank == 3:
        return "ka-lb-top3"
    return ""


def _render_event_board(event: str, gender: str) -> None:
    rows = get_pb_leaderboard_by_gender(event, gender)
    if not rows:
        render_empty_state("暫無有效成績紀錄", "學員提交並通過教練審核後會顯示於此")
        return

    for r in rows:
        rank = int(r["rank"])
        top = _top_card_class(rank)
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
        improve = r["improvement_text"]
        first = r["first_score"] if r["records_count"] >= 2 else "—"
        st.markdown(
            f"""<div class="ka-lb-card {top}">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;">
            <span class="ka-lb-rank">{medal} #{rank}</span>
            <div style="flex:1;min-width:120px;">
                <div style="font-size:1.25rem;font-weight:800;">{r['best_score']}</div>
                <div style="font-size:0.82rem;color:#64748b;">
                {r['best_date']} · 等級 {r['grade'] or '—'}
                </div>
            </div>
            <div style="font-size:0.78rem;color:#64748b;text-align:right;">
                首記 {first}<br>{improve}
            </div>
            </div></div>""",
            unsafe_allow_html=True,
        )


def render_leaderboard() -> None:
    render_page_header(
        "PB 排行榜",
        "按性別及項目顯示最佳成績（不顯示學員姓名）",
    )

    gender = st.radio("組別", GENDER_OPTIONS, horizontal=True, key="pb_leaderboard_gender")
    view_mode = st.radio(
        "顯示方式",
        ["單一項目", "全部項目"],
        horizontal=True,
        key="pb_leaderboard_mode",
    )

    if view_mode == "單一項目":
        event = st.selectbox("田徑項目", EVENTS, key="pb_leaderboard_event")
        st.markdown(f"#### {gender}子 · {event}")
        _render_event_board(event, gender)
    else:
        for event in EVENTS:
            rows = get_pb_leaderboard_by_gender(event, gender)
            if not rows:
                continue
            with st.expander(f"{event}（{len(rows)} 項成績）", expanded=event in ("100米", "200米", "400米")):
                _render_event_board(event, gender)

    st.caption("只計算風速有效之官方成績；至少兩次紀錄才顯示進步幅度；不公開選手姓名。")
