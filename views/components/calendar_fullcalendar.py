"""Student schedule — FullCalendar via streamlit-calendar."""

from __future__ import annotations

from datetime import date

import streamlit as st

from utils.config import normalize_train_type
from utils.helpers import safe_str
from views.components.calendar_theme import get_calendar_tones, inject_calendar_theme
from views.components.theme import get_ui_theme


def _parse_time_hm(raw: str) -> tuple[int, int] | None:
    text = safe_str(raw).strip()
    if not text or ":" not in text:
        return None
    parts = text.split(":", 1)
    try:
        return int(parts[0]), int(parts[1][:2])
    except ValueError:
        return None


def build_student_fullcalendar_events(
    prog_map: dict[str, dict],
    *,
    student_specialty: str,
    visible_day_fn,
    today: date | None = None,
) -> list[dict]:
    """Convert student-visible programs to FullCalendar event objects."""
    if today is None:
        today = date.today()
    today_str = today.isoformat()
    tones = get_calendar_tones()
    events: list[dict] = []
    for ds in sorted(prog_map.keys()):
        prog = visible_day_fn(prog_map, ds, student_specialty)
        if not prog:
            continue
        tp = normalize_train_type(safe_str(prog.get("type")))
        tone_key = "competition" if tp == "比賽" else "training"
        tone = tones.get(tone_key, tones["training"])
        if tp == "比賽":
            title = "比賽"
        elif ds > today_str:
            title = "訓練"
        else:
            title = safe_str(prog.get("title")) or "訓練"
        start_raw = safe_str(prog.get("start_time"))
        end_raw = safe_str(prog.get("end_time"))
        start_hm = _parse_time_hm(start_raw)
        end_hm = _parse_time_hm(end_raw)

        if start_hm:
            sh, sm = start_hm
            if end_hm:
                eh, em = end_hm
            else:
                eh, em = sh + 2 if sh < 22 else sh, sm
            event = {
                "id": ds,
                "title": title,
                "start": f"{ds}T{sh:02d}:{sm:02d}:00",
                "end": f"{ds}T{eh:02d}:{em:02d}:00",
                "allDay": False,
                "backgroundColor": tone["bg"],
                "borderColor": tone["accent"],
                "textColor": tone["fg"],
                "extendedProps": {"date": ds},
            }
        else:
            event = {
                "id": ds,
                "title": title,
                "start": ds,
                "allDay": True,
                "backgroundColor": tone["bg"],
                "borderColor": tone["accent"],
                "textColor": tone["fg"],
                "extendedProps": {"date": ds},
            }
        events.append(event)
    return events


def render_student_fullcalendar(
    *,
    year: int,
    month: int,
    events: list[dict],
    select_key: str = "student_sched_selected",
) -> str | None:
    """
    Render FullCalendar month view. Returns selected date (YYYY-MM-DD) if user clicked.
    """
    try:
        from streamlit_calendar import calendar as fc_calendar
    except ImportError:
        st.warning("FullCalendar 檢視需要安裝 `streamlit-calendar`，請重新部署後再試。")
        st.code("pip install streamlit-calendar", language="bash")
        return None

    inject_calendar_theme()
    dark = get_ui_theme() == "dark"
    initial_date = f"{year}-{month:02d}-01"

    options = {
        "initialView": "dayGridMonth",
        "initialDate": initial_date,
        "headerToolbar": False,
        "height": "auto",
        "firstDay": 0,
        "locale": "zh-tw",
        "dayMaxEvents": 3,
        "fixedWeekCount": False,
        "selectMirror": True,
    }

    custom_css = """
    .fc .fc-daygrid-day-number { font-size: 0.85rem; font-weight: 700; }
    .fc .fc-event { font-size: 0.72rem; font-weight: 700; border-radius: 4px; }
    .fc .fc-daygrid-event { margin-top: 1px; }
    """
    if dark:
        custom_css += """
        .fc { --fc-border-color: #334155; --fc-page-bg-color: #1a1d24;
              --fc-neutral-bg-color: #141820; --fc-list-event-hover-bg-color: #1e293b; }
        .fc .fc-daygrid-day-number { color: #e2e8f0; }
        .fc-theme-standard td, .fc-theme-standard th { border-color: #334155; }
        """

    state = fc_calendar(
        events=events,
        options=options,
        custom_css=custom_css,
        key=f"student_fc_{year}_{month}",
    )

    selected: str | None = None
    if isinstance(state, dict):
        callback = state.get("callback")
        if callback == "eventClick":
            ev = (state.get("eventClick") or {}).get("event") or {}
            start = safe_str(ev.get("start"))
            selected = start[:10] if start else None
            ext = ev.get("extendedProps") or {}
            selected = safe_str(ext.get("date")) or selected
        elif callback == "dateClick":
            dc = state.get("dateClick") or {}
            start = safe_str(dc.get("date"))
            selected = start[:10] if start else None

    if selected:
        st.session_state[select_key] = selected
    return selected or st.session_state.get(select_key)
