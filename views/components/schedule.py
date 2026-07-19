"""Training timetable — student calendar & coach preview list."""

import calendar
from datetime import date

import streamlit as st

from utils.config import (
    CALENDAR_BG_COMPETITION,
    CALENDAR_BG_EMPTY,
    CALENDAR_BG_REST,
    CALENDAR_BG_TRAINING,
    SPECIALTY_TO_GROUP,
    normalize_train_type,
)
from utils.data_store import (
    build_coach_prog_map,
    get_attendance_map_for_month,
    get_attendance_record,
    get_programs_for_month,
    get_timetable_entries,
    program_visible_to_student,
    build_student_prog_map,
)
from utils.helpers import (
    calendar_cell_bg,
    calendar_cell_tone,
    format_timetable_date,
    format_train_duration,
    normalize_date_str,
    program_specs,
    resolve_venue,
    safe_int,
    safe_str,
    workout_detail,
)
from views.components.calendar_compact import open_dialog_if_requested, render_compact_month_grid
from views.components.calendar_list import render_view_mode_toggle


def _type_bg(prog: dict) -> str:
    return calendar_cell_bg(prog)


def _time_venue_text(prog: dict) -> tuple[str, str]:
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    time_text = f"{start} – {end}" if start and end else (start or end or "時間待通知")
    return time_text, resolve_venue(prog)


def _student_prog_for_day(prog_map: dict[str, dict], ds: str, specialty: str) -> dict | None:
    from utils.helpers import has_time_venue, has_workout_plan

    prog = prog_map.get(ds)
    if not prog:
        return None
    if not program_visible_to_student(prog, specialty):
        return None
    tp = normalize_train_type(safe_str(prog.get("type")))
    if tp == "休息":
        return None
    if tp == "待排課":
        return prog if has_time_venue(prog) else None
    if has_workout_plan(prog) or has_time_venue(prog):
        return prog
    return None


def _render_time_venue_block(prog: dict, date_label: str, *, bg: str) -> None:
    time_text, venue = _time_venue_text(prog)
    st.markdown(
        f"<div style='background:{bg};border:1px solid #cbd5e1;border-radius:8px;padding:12px 14px;'>"
        f"<div style='font-size:13px;font-weight:600;color:#334155;'>{date_label}</div>"
        f"<div style='font-size:14px;margin-top:8px;'>🕐 <b>{time_text}</b></div>"
        f"<div style='font-size:14px;margin-top:4px;'>📍 <b>{venue}</b></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _attendance_line(att: dict | None) -> str:
    if not att:
        return ""
    if att.get("status") == "present":
        dur = safe_int(att.get("duration_minutes"), 0)
        if dur > 0:
            return f"✅ {format_train_duration(dur)}"
        return "✅ 已簽到"
    if att.get("status") == "leave":
        return "📝 請假"
    return ""


def _render_day_detail_content(
    selected: str,
    prog_map: dict[str, dict],
    student_specialty: str,
    today: date,
    student_name: str = "",
    *,
    show_heading: bool = True,
) -> None:
    """Training detail body — used inline or inside st.dialog."""
    today_str = today.isoformat()
    sel_d = date.fromisoformat(selected)
    date_label = format_timetable_date(selected)
    prog = _student_prog_for_day(prog_map, selected, student_specialty)

    if show_heading:
        if selected == today_str:
            st.markdown(f"### 📍 今日訓練 · {date_label}")
        else:
            st.markdown(f"### 📅 {date_label}")

    if not prog:
        st.info(f"**{date_label}** — 休息或無你的組別訓練。")
        return

    detail = workout_detail(prog)
    time_text, venue = _time_venue_text(prog)
    att = get_attendance_record(student_name, selected) if student_name else None
    att_line = _attendance_line(att)

    if sel_d < today:
        st.caption("ℹ️ 過往訓練")

    if detail:
        st.markdown("**跑案內容**")
        st.markdown(detail)
    else:
        st.markdown("**訓練**")

    st.markdown(f"🕐 **{time_text}**")
    st.markdown(f"📍 **{venue}**")

    if att_line:
        if att and att.get("status") == "present":
            st.success(f"{att_line} · {att.get('detail', '')}")
        elif att and att.get("status") == "leave":
            st.info(att_line)

    tips = safe_str(prog.get("tips"))
    if tips:
        st.markdown("---")
        st.caption(f"教練備註：{tips}")


def _render_selected_day_detail(
    selected: str,
    prog_map: dict[str, dict],
    student_specialty: str,
    today: date,
    student_name: str = "",
) -> None:
    _render_day_detail_content(
        selected, prog_map, student_specialty, today, student_name, show_heading=True
    )


def _time_hint(prog: dict) -> str:
    """Short time/venue preview for calendar cell."""
    start = safe_str(prog.get("start_time"))
    venue = resolve_venue(prog)
    parts: list[str] = []
    if start:
        parts.append(start[:5] if len(start) >= 5 else start)
    if venue and venue not in ("（待設定）", "（待通知）"):
        short = venue if len(venue) <= 5 else venue[:4] + "…"
        parts.append(short)
    return "·".join(parts)


def _student_compact_style(
    ds: str,
    day: int,
    prog_map: dict[str, dict],
    student_specialty: str,
    att_map: dict[str, dict],
    today: date,
) -> dict:
    """Style one compact calendar cell."""
    today_str = today.isoformat()
    d = date.fromisoformat(ds)
    is_today = ds == today_str
    prog = _student_prog_for_day(prog_map, ds, student_specialty)
    att = att_map.get(ds)

    if is_today:
        border = "2px solid #1d4ed8"
        label = f"●{day}"
    else:
        border = "1px solid #e2e8f0"
        label = str(day)

    if prog:
        tone = calendar_cell_tone(prog)
        hint = _time_hint(prog)
        if att and att.get("status") == "present" and d < today:
            border = "2px solid #16a34a"
    elif att and att.get("status") == "present":
        tone = "attended"
        hint = ""
    elif d > today:
        tone = "rest"
        hint = ""
    else:
        tone = "empty"
        hint = ""

    return {
        "tone": tone,
        "bg": calendar_cell_bg(prog),
        "border": border,
        "label": label,
        "disabled": False,
        "hint": hint,
    }


def _render_student_schedule_compact(
    year: int,
    month: int,
    prog_map: dict[str, dict],
    student_specialty: str,
    att_map: dict[str, dict],
    today: date,
    student_name: str,
) -> None:
    if "student_sched_selected" not in st.session_state:
        st.session_state.student_sched_selected = today.isoformat()

    def _style(ds: str, day: int) -> dict:
        return _student_compact_style(ds, day, prog_map, student_specialty, att_map, today)

    render_compact_month_grid(
        year=year,
        month=month,
        select_key="student_sched_selected",
        dialog_key="student_sched_dialog",
        day_style=_style,
    )

    open_dialog_if_requested(
        "student_sched_dialog",
        lambda ds: _render_day_detail_content(
            ds,
            prog_map,
            student_specialty,
            today,
            student_name,
            show_heading=True,
        ),
    )


def _student_day_cell(
    ds: str,
    prog_map: dict[str, dict],
    student_specialty: str,
    att_map: dict[str, dict],
    today: date,
) -> tuple[str, str, str, str, str]:
    """Return title, detail, type_label, bg, btn_label for one calendar day."""
    today_str = today.isoformat()
    d = date.fromisoformat(ds)
    is_today = ds == today_str
    prog = _student_prog_for_day(prog_map, ds, student_specialty)
    att = att_map.get(ds)
    att_line = _attendance_line(att)

    if prog:
        time_part, venue = _time_venue_text(prog)
        detail_parts = [p for p in (time_part, venue) if p and p not in ("時間待通知", "（待設定）", "（待通知）")]
        detail = " · ".join(detail_parts)
        if att_line:
            detail = f"{detail} · {att_line}" if detail else att_line
        tp = normalize_train_type(safe_str(prog.get("type")))
        bg = calendar_cell_bg(prog)
        title = "比賽" if tp == "比賽" else "訓練"
        if is_today:
            return f"🔵 {title}", detail, title, bg, f"🔵 {d.day}"
        if d > today:
            return title, detail, title, bg, str(d.day)
        if att and att.get("status") == "present":
            return "✅ 已訓練", detail, title, "#dcfce7", str(d.day)
        return "已過", detail, title, "#e2e8f0", str(d.day)

    if is_today:
        detail = att_line or ""
        return "🔵 休息", detail, "休息", CALENDAR_BG_REST, f"🔵 {d.day}"

    if att_line:
        title = "已簽到" if att and att.get("status") == "present" else "—"
        bg = "#dcfce7" if att and att.get("status") == "present" else "#f8fafc"
        return title, att_line, "—", bg, str(d.day)
    return "—", "", "休息", "#f8fafc", str(d.day)


def _render_student_schedule_list(
    year: int,
    month: int,
    prog_map: dict[str, dict],
    student_specialty: str,
    att_map: dict[str, dict],
    today: date,
) -> None:
    if "student_sched_selected" not in st.session_state:
        st.session_state.student_sched_selected = today.isoformat()

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    wd_names = ["一", "二", "三", "四", "五", "六", "日"]

    for week in weeks:
        for day in week:
            if day == 0:
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            d = date.fromisoformat(ds)
            title_line, detail_line, type_label, bg, _btn = _student_day_cell(
                ds, prog_map, student_specialty, att_map, today
            )
            wd_cn = wd_names[d.weekday()]
            selected = st.session_state.get("student_sched_selected") == ds
            border = "2px solid #1d4ed8" if selected else "1px solid #e2e8f0"

            type_badge = (
                f"<span style='background:#e2e8f0;color:#334155;padding:2px 8px;"
                f"border-radius:999px;font-size:12px;margin-left:8px;'>{type_label}</span>"
                if type_label and type_label != "—" else ""
            )
            detail_html = (
                f"<div style='font-size:13px;color:#64748b;margin-top:6px;'>{detail_line}</div>"
                if detail_line else ""
            )

            label_col, btn_col = st.columns([5, 1])
            with label_col:
                st.markdown(
                    f"<div style='background:{bg};border:{border};border-radius:10px;"
                    f"padding:12px 14px;margin-bottom:6px;'>"
                    f"<div style='font-size:15px;font-weight:700;color:#1e3a8a;'>"
                    f"{month}/{day:02d}（{wd_cn}）{type_badge}</div>"
                    f"<div style='font-size:14px;font-weight:600;margin-top:4px;'>{title_line}</div>"
                    f"{detail_html}</div>",
                    unsafe_allow_html=True,
                )
            with btn_col:
                if st.button("選", key=f"student_sched_list_{ds}", use_container_width=True):
                    st.session_state.student_sched_selected = ds
                    st.rerun()


def render_student_schedule_calendar(student_specialty: str = "", student_name: str = "") -> None:
    """Month calendar; full content today only; time/venue for all training days."""
    today = date.today()
    today_str = today.isoformat()

    if "student_sched_year" not in st.session_state:
        st.session_state.student_sched_year = today.year
        st.session_state.student_sched_month = today.month

    year = st.session_state.student_sched_year
    month = st.session_state.student_sched_month

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 上月", key="student_sched_prev"):
        if month == 1:
            st.session_state.student_sched_month, st.session_state.student_sched_year = 12, year - 1
        else:
            st.session_state.student_sched_month -= 1
        st.rerun()
    c2.markdown(f"### {year} 年 {month:02d} 月")
    if c3.button("下月 ▶", key="student_sched_next"):
        if month == 12:
            st.session_state.student_sched_month, st.session_state.student_sched_year = 1, year + 1
        else:
            st.session_state.student_sched_month += 1
        st.rerun()

    mapped = SPECIALTY_TO_GROUP.get(student_specialty, "—")
    st.caption(
        f"顯示 **全體組員** 及 **{mapped}** · "
        f"🔵 藍色=訓練 · 🔴 紅色=比賽 · 點選查看跑案、時間與地點"
    )

    programs = get_programs_for_month(year, month)
    att_map = get_attendance_map_for_month(student_name, year, month) if student_name else {}
    total_minutes = sum(
        safe_int(v.get("duration_minutes"), 0)
        for v in att_map.values()
        if v.get("status") == "present"
    )
    if student_name and total_minutes > 0:
        st.caption(f"本月累計訓練：**{format_train_duration(total_minutes)}**（已簽到日）")

    prog_map = build_student_prog_map(programs, student_specialty)

    view_mode = render_view_mode_toggle("student_sched", default_mode="list")
    if view_mode == "list":
        _render_student_schedule_list(year, month, prog_map, student_specialty, att_map, today)
        st.markdown("---")
        selected = st.session_state.get("student_sched_selected", today_str)
        _render_selected_day_detail(selected, prog_map, student_specialty, today, student_name)
    else:
        _render_student_schedule_compact(
            year, month, prog_map, student_specialty, att_map, today, student_name
        )

    st.caption("💡 月曆為 7 格一列；🔵 藍色=訓練、🔴 紅色=比賽；點方格查看完整跑案。")


def _entry_card(prog: dict, *, highlight: bool = False) -> str:
    tp = normalize_train_type(safe_str(prog.get("type"))) or "訓練"
    bg = calendar_cell_bg(prog)
    border = "2px solid #1d4ed8" if highlight else "1px solid #e2e8f0"
    title = safe_str(prog.get("title")) or tp or "訓練"
    specs = program_specs(prog)
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    time_text = f"{start} – {end}" if start and end else (start or end or "時間待設定")
    venue = resolve_venue(prog)
    group = safe_str(prog.get("group"))
    specs_html = f"<div style='color:#475569;font-size:11px;margin-top:2px;'>{specs}</div>" if specs else ""
    return (
        f"<div style='background:{bg};border:{border};border-radius:8px;padding:10px 12px;margin-bottom:8px;'>"
        f"<div style='font-size:12px;color:#334155;font-weight:600;'>{format_timetable_date(prog['date'])}"
        f"{' · 今日' if highlight else ''}</div>"
        f"<div style='font-size:13px;font-weight:700;color:#1e3a8a;margin-top:4px;'>{tp}</div>"
        f"{specs_html}"
        f"<div style='color:#334155;font-size:12px;margin-top:6px;'>🕐 {time_text}</div>"
        f"<div style='color:#475569;font-size:12px;margin-top:2px;'>📍 {venue}</div>"
        f"<div style='color:#64748b;font-size:10px;margin-top:4px;'>👥 {group}</div>"
        f"</div>"
    )


def render_program_timetable(
    *,
    student_specialty: str | None = None,
    days_ahead: int = 45,
) -> None:
    """Coach preview — list upcoming training days with time & venue."""
    entries = get_timetable_entries(specialty=student_specialty, days_ahead=days_ahead)
    today = date.today().isoformat()

    if student_specialty:
        mapped = SPECIALTY_TO_GROUP.get(student_specialty, "—")
        st.caption(f"顯示 **全體組員** 及 **{mapped}** 的課表（教練預覽）")

    if not entries:
        st.info("月曆中尚無訓練課表，請先在「週期化課表」排課。")
        return

    html = "".join(_entry_card(p, highlight=p["date"] == today) for p in entries)
    st.markdown(html, unsafe_allow_html=True)
    st.caption("🔵 藍色=訓練 · 🔴 紅色=比賽")
