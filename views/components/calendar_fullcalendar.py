"""FullCalendar views via streamlit-calendar."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone

import streamlit as st

from utils.config import normalize_train_type
from utils.helpers import safe_str
from views.components.calendar_theme import get_calendar_tones, inject_calendar_theme
from views.components.theme import get_ui_theme

# App audience is Hong Kong — FullCalendar often emits UTC midnight for day clicks.
_APP_TZ = timezone(timedelta(hours=8))

# Injected into streamlit-calendar iframe (styled-components scoped wrapper).
_FC_DARK_CUSTOM_CSS = """
background-color: #1a1a1a !important;
color: #ffffff;
.fc, .fc * {
    --fc-page-bg-color: #1a1a1a;
    --fc-neutral-bg-color: #1a1a1a;
    --fc-border-color: #666666;
    --fc-today-bg-color: #2a2a2a;
    --fc-list-event-hover-bg-color: #1a1a1a;
}
.fc .fc-scrollgrid,
.fc .fc-scrollgrid-section > td,
.fc .fc-scrollgrid-sync-table,
.fc .fc-col-header-cell,
.fc .fc-daygrid-day,
.fc .fc-daygrid-day-frame,
.fc .fc-daygrid-day-bg,
.fc .fc-daygrid-day-top,
.fc-theme-standard td,
.fc-theme-standard th {
    background: #1a1a1a !important;
    background-color: #1a1a1a !important;
    border-color: #666666 !important;
}
.fc .fc-daygrid-day-number {
    color: #ffffff !important;
}
.fc .fc-col-header-cell-cushion {
    color: #cccccc !important;
}
.fc .fc-day-today,
.fc .fc-day-today .fc-daygrid-day-frame,
.fc .fc-day-today .fc-daygrid-day-bg {
    background: #2a2a2a !important;
    background-color: #2a2a2a !important;
}
.fc .fc-daygrid-day:hover,
.fc .fc-daygrid-day:active,
.fc .fc-daygrid-day.fc-day-selected,
.fc .fc-highlight {
    background: #1a1a1a !important;
    background-color: #1a1a1a !important;
}
.fc .fc-event:hover,
.fc .fc-event:active {
    filter: none !important;
    opacity: 1 !important;
}
"""

# Parent-page patch for the component iframe (:root inside iframe document).
_FC_DARK_IFRAME_CSS = (
    ":root{--fc-page-bg-color:#1a1a1a;--fc-neutral-bg-color:#1a1a1a;"
    "--fc-border-color:#666666;--fc-today-bg-color:#2a2a2a;"
    "--fc-list-event-hover-bg-color:#1a1a1a;}"
    ".fc,.fc-scrollgrid,.fc-scrollgrid-sync-table,.fc-daygrid-day,"
    ".fc-daygrid-day-frame,.fc-daygrid-day-bg,.fc-col-header-cell,"
    ".fc-theme-standard td,.fc-theme-standard th{"
    "background:#1a1a1a!important;background-color:#1a1a1a!important;"
    "border-color:#666666!important;}"
    ".fc-day-today,.fc-day-today .fc-daygrid-day-frame{"
    "background:#2a2a2a!important;background-color:#2a2a2a!important;}"
    ".fc-daygrid-day-number{color:#ffffff!important;}"
    ".fc-col-header-cell-cushion{color:#cccccc!important;}"
    ".fc-highlight,.fc-daygrid-day:hover,.fc-daygrid-day:active{"
    "background:#1a1a1a!important;background-color:#1a1a1a!important;}"
)


def _parse_time_hm(raw: str) -> tuple[int, int] | None:
    text = safe_str(raw).strip()
    if not text or ":" not in text:
        return None
    parts = text.split(":", 1)
    try:
        return int(parts[0]), int(parts[1][:2])
    except ValueError:
        return None


def parse_fullcalendar_clicked_date(
    *,
    date_str: str | None = None,
    raw_date: str | None = None,
    extended_date: str | None = None,
) -> str | None:
    """Normalize FullCalendar click payloads to YYYY-MM-DD in local (HKT) calendar.

    streamlit-calendar / FullCalendar frequently returns UTC ISO strings such as
    ``2026-07-23T16:00:00.000Z`` when the user taps the 24th in Hong Kong (UTC+8).
    Taking ``[:10]`` then wrongly selects the 23rd.
    """
    for candidate in (extended_date, date_str):
        text = safe_str(candidate).strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return text[:10]

    text = safe_str(raw_date).strip()
    if not text:
        return None
    if len(text) >= 10 and "T" not in text and text[4] == "-" and text[7] == "-":
        return text[:10]

    try:
        normalized = text.replace("Z", "+00:00") if text.endswith("Z") else text
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            # Naive datetime: trust the calendar date part (local wall time).
            return text[:10]
        return dt.astimezone(_APP_TZ).date().isoformat()
    except ValueError:
        return text[:10] if len(text) >= 10 else None


def _inject_fullcalendar_dark_iframe() -> None:
    """Patch FullCalendar iframe — parent CSS cannot reach component documents."""
    if get_ui_theme() != "dark":
        return
    css_json = json.dumps(_FC_DARK_IFRAME_CSS)
    try:
        st.html(
            f"""
            <script>
            (function () {{
              var CSS = {css_json};
              function patch() {{
                document.querySelectorAll('iframe').forEach(function (fr) {{
                  try {{
                    var doc = fr.contentDocument;
                    if (!doc || !doc.querySelector('.fc')) return;
                    var el = doc.getElementById('ka-fc-dark-patch');
                    if (!el) {{
                      el = doc.createElement('style');
                      el.id = 'ka-fc-dark-patch';
                      doc.head.appendChild(el);
                    }}
                    el.textContent = CSS;
                  }} catch (e) {{}}
                }});
              }}
              patch();
              setTimeout(patch, 120);
              setTimeout(patch, 500);
              setTimeout(patch, 1500);
            }})();
            </script>
            """,
            unsafe_allow_javascript=True,
        )
    except TypeError:
        pass
    except Exception:
        pass


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
        custom_css += _FC_DARK_CUSTOM_CSS

    state = fc_calendar(
        events=events,
        options=options,
        custom_css=custom_css,
        key=f"{fc_key_prefix}_{year}_{month}",
    )

    if dark:
        _inject_fullcalendar_dark_iframe()

    selected: str | None = None
    if isinstance(state, dict):
        callback = state.get("callback")
        if callback == "eventClick":
            ev = (state.get("eventClick") or {}).get("event") or {}
            ext = ev.get("extendedProps") or {}
            selected = parse_fullcalendar_clicked_date(
                extended_date=safe_str(ext.get("date")),
                date_str=safe_str(ev.get("startStr") or ev.get("dateStr")),
                raw_date=safe_str(ev.get("start")),
            )
        elif callback == "dateClick":
            dc = state.get("dateClick") or {}
            selected = parse_fullcalendar_clicked_date(
                date_str=safe_str(dc.get("dateStr")),
                raw_date=safe_str(dc.get("date")),
            )

    if selected:
        prev = st.session_state.get(select_key)
        st.session_state[select_key] = selected
        if goto_edit_session_key:
            already_edit = (
                st.session_state.get(goto_edit_session_key) == "edit"
                and prev == selected
            )
            st.session_state[goto_edit_session_key] = "edit"
            # Screen is read before calendar render — force a second pass into edit UI
            if not already_edit:
                st.rerun()
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
