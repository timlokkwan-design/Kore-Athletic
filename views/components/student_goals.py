"""Student season goals — pick event, set target time/score on homepage."""
from __future__ import annotations

import streamlit as st

from utils.config import EVENTS, FIELD_EVENTS
from utils.data_store import (
    deactivate_student_goal,
    get_active_goals_for_user,
    resolve_event_pb,
    upsert_student_goal,
)
from utils.helpers import safe_str


def _score_hint(event: str) -> str:
    if event in FIELD_EVENTS:
        return "例如 6.50（米）"
    if event in ("800米", "1500米", "3000米", "5000米"):
        return "例如 2:05.00 或 125.0"
    return "例如 11.50"


def render_student_goals(user: dict, *, show_title: bool = True) -> None:
    """Compact goal block for the student homepage (訓練時間表)."""
    username = safe_str(user.get("username"))
    name = safe_str(user.get("name"))
    if not username or not name:
        return

    try:
        goals = get_active_goals_for_user(username)
    except Exception:
        st.caption("目標功能暫時未能載入。若剛更新，請教練於 Supabase 執行 schema_patch_v202.sql。")
        return

    if show_title:
        st.markdown(
            '<div class="ka-goal-wrap"><p class="ka-goal-title">🎯 我的目標</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="ka-goal-wrap">', unsafe_allow_html=True)

    if goals.empty:
        st.markdown(
            '<p class="ka-goal-empty">尚未訂立目標 — 揀項目、輸入目標時間，幫自己定方向。</p>',
            unsafe_allow_html=True,
        )
    else:
        for _, row in goals.iterrows():
            event = safe_str(row.get("event"))
            target = safe_str(row.get("target_score"))
            pb = resolve_event_pb(name, event)
            pb_score = safe_str(pb.get("score"))
            unit = "米" if event in FIELD_EVENTS else ""
            label = "目標成績" if event in FIELD_EVENTS else "目標時間"
            pb_line = f"目前 PB：{pb_score}{unit}" if pb_score else "尚無 PB"
            goal_id = safe_str(row.get("id"))
            st.markdown(
                f'<div class="ka-goal-card">'
                f'<div><div class="ka-goal-event">{event}</div>'
                f'<div class="ka-goal-meta">{label} <b>{target}{unit}</b> · {pb_line}</div></div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "移除目標",
                key=f"stu_goal_rm_{goal_id}",
                use_container_width=True,
                type="secondary",
            ):
                ok, msg = deactivate_student_goal(goal_id, username)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with st.expander("➕ 新增／更新目標", expanded=goals.empty):
        event = st.selectbox("項目", EVENTS, key="stu_goal_event")
        is_field = event in FIELD_EVENTS
        label = "目標成績" if is_field else "目標時間"
        target = st.text_input(
            label,
            key="stu_goal_target",
            placeholder=_score_hint(event),
            help="徑賽用秒或分:秒；田賽用米數",
        )
        if st.button("儲存目標", type="primary", use_container_width=True, key="stu_goal_save"):
            ok, msg = upsert_student_goal(
                username=username,
                athlete_name=name,
                event=event,
                target_score=target,
            )
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)
