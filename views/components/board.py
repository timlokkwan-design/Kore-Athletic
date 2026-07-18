"""Shared KORE ATHLETIC training announcement board."""

from datetime import date, datetime

import streamlit as st

from utils.config import APP_NAME, COACH_NAME
from utils.data_store import (
    days_until_competition,
    ensure_program_dict,
    get_program,
    get_programs_for_date,
    load_periodization,
    log_completion_rate,
)
from utils.helpers import safe_int, safe_str, short_group_label
from views.components.brand import render_brand_header as _render_brand_header


def render_brand_header() -> None:
    _render_brand_header(compact=True)


def render_training_board(show_specs: bool = True, specialty: str | None = None) -> None:
    """V6-style 訓練計劃看板."""
    prog = ensure_program_dict(get_program(specialty=specialty))
    per = load_periodization()
    countdown = days_until_competition()
    today_label = datetime.now().strftime("%Y年%m月%d日 %A")

    phase = safe_str(prog.get("phase")) or safe_str(per.get("global_phase"))
    theme = safe_str(prog.get("week_theme")) or safe_str(per.get("global_week_theme"))
    specs_parts = []
    sets, reps, dist = safe_int(prog.get("sets")), safe_int(prog.get("reps")), safe_int(prog.get("dist"))
    if sets and reps and dist:
        specs_parts.append(f"{sets}x{reps}x{dist}m")
    elif reps and dist:
        specs_parts.append(f"{dist}m × {reps}")
    rest = safe_str(prog.get("rest"))
    if rest:
        specs_parts.append(rest)
    specs = " | ".join(specs_parts) if specs_parts else "-"

    st.markdown("##### 📋 訓練計劃看板")
    st.caption(today_label)

    if countdown is not None:
        st.info(f"🏁 距校際賽 / 學界還有 **{countdown}** 天（{per['comp_target_date']}）")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("訓練類型", safe_str(prog.get("type"), "-"))
    group = safe_str(prog.get("group"), "-")
    col2.metric("組別", group[:8] + "…" if len(group) > 8 else group)
    col3.metric("階段", phase)
    col4.metric("週主題", theme)

    st.markdown(
        f"""
        <div style="background:#eff6ff;border:1px solid #93c5fd;border-radius:8px;padding:1rem;">
        <p style="margin:0;font-size:1.1rem;font-weight:bold;">🏋️ {safe_str(prog.get('type'), '今日無課表')}</p>
        {"<p style='margin:0.5rem 0 0;font-size:0.85rem;font-family:monospace;'>規格：" + specs + "</p>" if show_specs else ""}
        <p style="margin:0.75rem 0 0;font-size:0.9rem;font-style:italic;">
        <strong>教練提示（{COACH_NAME}）：</strong>{safe_str(prog.get('tips'), '依教練指示完成')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rate = log_completion_rate(date.today())
    st.caption(f"今日訓練回報完成率：{rate}%")


def render_whatsapp_program_copy() -> None:
    """Coach tool: copy program text for WhatsApp."""
    prog = get_program()
    per = load_periodization()
    phase = prog.get("phase") or per["global_phase"]
    theme = prog.get("week_theme") or per["global_week_theme"]
    text = (
        f"🏃 {APP_NAME} 訓練課表\n"
        f"📅 {prog['date']}\n"
        f"📋 {prog.get('title')} ({prog.get('type')})\n"
        f"👥 {prog.get('group')}\n"
        f"📊 階段:{phase} | 主題:{theme}\n"
        f"💡 {prog.get('tips') or '依教練指示'}\n"
        f"— {COACH_NAME}教練"
    )
    st.code(text, language=None)
