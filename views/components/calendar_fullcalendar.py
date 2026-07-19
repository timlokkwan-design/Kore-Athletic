"""FullCalendar views via streamlit-calendar."""

from __future__ import annotations

from collections.abc import Callable
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


def _prog_to_fc_event(ds: str, prog: dict, *, title: str, tone_key: str) -> dict:
    tones = get_calendar_tones()
    tone = tones.get(tone_key, tones["training"])
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
        return {
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
    return {
        "id": ds,
        "title": title,
        "start": ds,
        "allDay": True,
        "backgroundColor": tone["bg"],
        "borderColor": tone["accent"],
        "textColor": tone["fg"],
        "extendedProps": {"date": ds},
    }


def build_coach_program_fc_events(
    prog_map: dict[str, dict],
    *,
    title_fn: Callable[[str, dict], str],
    tone_fn: Callable[[str, dict], str] | None = None,
) -> list[dict]:
    events: list[dict] = []
    for ds in sorted(prog_map.keys()):
        prog = prog_map.get(ds)
        if not prog:
            continue
        tp = normalize_train_type(safe_str(prog.get("type")))
        if tp == "休息":
            continue
        tone_key = tone_fn(ds, prog) if tone_fn else ("competition" if tp == "比賽" else "training")
        title = title_fn(ds, prog)
        events.append(_prog_to_fc_event(ds, prog, title=title, tone_key=tone_key))
    return events


def build_coach_schedule_fc_events(
    day_map: dict[str, list[dict]],
    *,
    title_fn: Callable[[str, list[dict]], str],
) -> list[dict]:
    events: list[dict] = []
    for ds in sorted(day_map.keys()):
        progs = day_map.get(ds) or []
        active = [
            p for p in progs
            if normalize_train_type(safe_str(p.get("type"))) not in ("休息",)
        ]
        if not active:
            continue
        ref = active[0]
        tp = normalize_train_type(safe_str(ref.get("type")))
        tone_key = "competition" if tp == "比賽" else "training"
        title = title_fn(ds, progs)
        events.append(_prog_to_fc_event(ds, ref, title=title, tone_key=tone_key))
    return events


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
    events: list[dict] = []
    for ds in sorted(prog_map.keys()):
        prog = visible_day_fn(prog_map, ds, student_specialty)
        if not prog:
            continue
        tp = normalize_train_type(safe_str(prog.get("type")))
        tone_key = "competition" if tp == "比賽" else "training"
        if tp == "比賽":
            title = "比賽"
        elif ds > today_str:
            title = "訓練"
        else:
            title = safe_str(prog.get("title")) or "訓練"
        events.append(_prog_to_fc_event(ds, prog, title=title, tone_key=tone_key))
    return events


def render_fullcalendar(
    *,
    year: int,
    month: int,
    events: list[dict],
    select_key: str = "student_sched_selected",
    fc_key_prefix: str = "fc",
    goto_edit_session_key: str | None = None,
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
        key=f"{fc_key_prefix}_{year}_{month}",
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
        if goto_edit_session_key:
            st.session_state[goto_edit_session_key] = "edit"
    return selected or st.session_state.get(select_key)


def render_student_fullcalendar(
    *,
    year: int,
    month: int,
    events: list[dict],
    select_key: str = "student_sched_selected",
) -> str | None:
    return render_fullcalendar(
        year=year,
        month=month,
        events=events,
        select_key=select_key,
        fc_key_prefix="student_fc",
    )
