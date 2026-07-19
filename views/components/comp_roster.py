"""Shared competition registration roster UI — 成功報名名單."""
from __future__ import annotations

import streamlit as st

from utils.data_store import get_comp_entries_for_comp
from utils.helpers import safe_str
from views.components.theme import render_empty_state


def _events_text(events: list[str]) -> str:
    return "、".join(events) if events else "—"


def render_successful_registration_roster(comp_id: str, *, title: str = "成功報名名單") -> None:
    """Show athletes who successfully registered for a competition."""
    entries = get_comp_entries_for_comp(comp_id)
    st.markdown(f"**{title}**")
    if not entries:
        render_empty_state("暫未有成功報名", "學生提交報名後會顯示於此")
        return
    st.caption(f"共 {len(entries)} 人")
    for entry in entries:
        name = safe_str(entry.get("athlete_name")) or "—"
        events = _events_text(entry.get("events") or [])
        st.markdown(f"• **{name}** — {events}")
