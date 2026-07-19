"""V6-style month calendar grid."""

from datetime import date
from typing import Callable

import streamlit as st

from utils.acwr import acwr_status, calc_acwr
from utils.data_store import (
    build_coach_prog_map,
    ensure_program_dict,
    filter_programs_by_group,
    get_all_logs,
    get_programs_for_month,
    get_student_names,
    row_to_program,
)
from utils.helpers import (
    day_sync_status,
    format_timetable_date,
    format_time_venue_line,
    calendar_cell_bg,
    calendar_cell_tone,
    calendar_day_event_chips,
    normalize_date_str,
    program_calendar_summary,
    resolve_venue,
    safe_str,
    short_group_label,
    sync_status_label,
    sync_status_priority,
    workout_detail,
    is_coach_plan_day,
)
from views.components.calendar_compact import open_dialog_if_requested
from views.components.calendar_fullcalendar import build_coach_program_fc_events, render_fullcalendar
from views.components.calendar_timetree import render_timetree_month_grid
from views.components.calendar_list import render_month_day_list, render_view_mode_toggle
from views.components.calendar_theme import inject_calendar_theme
from views.components.calendar_ui import calendar_shell, render_calendar_month_nav
from views.components.coach_mobile_ui import render_calendar_legend
from utils.coach_calendar_state import (
    ensure_coach_calendar_state,
    get_coach_calendar_year_month,
    set_coach_calendar_date,
    set_coach_calendar_month,
)


def _sync_selection_to_month(select_key: str, year: int, month: int) -> None:
    """Keep selected date within the visible calendar month."""
    cur = st.session_state.get(select_key, date.today().isoformat())
    try:
        sel = date.fromisoformat(str(cur))
    except ValueError:
        sel = date.today()
    if sel.year == year and sel.month == month:
        return
    today = date.today()
    if today.year == year and today.month == month:
        ds = today.isoformat()
    else:
        ds = f"{year}-{month:02d}-01"
    st.session_state[select_key] = ds
    set_coach_calendar_date(ds)


def _toggle_copy_target(ds: str, copy_source: str) -> None:
    if ds == copy_source:
        st.session_state["copy_flash"] = ("error", "來源日期不能選為目標")
        return
    targets = list(st.session_state.get("copy_target_dates", []))
    if ds in targets:
        targets.remove(ds)
    else:
        targets.append(ds)
    st.session_state.copy_target_dates = sorted(targets)


def _toggle_delete_target(ds: str) -> None:
    targets = list(st.session_state.get("delete_target_dates", []))
    if ds in targets:
        targets.remove(ds)
    else:
        targets.append(ds)
    st.session_state.delete_target_dates = sorted(targets)


def _calendar_prev_month(select_key: str, copy_mode: bool, delete_mode: bool) -> None:
    year, month = get_coach_calendar_year_month()
    if month == 1:
        year, month = year - 1, 12
    else:
        month -= 1
    set_coach_calendar_month(year, month)
    if not copy_mode and not delete_mode:
        _sync_selection_to_month(select_key, year, month)


def _calendar_next_month(select_key: str, copy_mode: bool, delete_mode: bool) -> None:
    year, month = get_coach_calendar_year_month()
    if month == 12:
        year, month = year + 1, 1
    else:
        month += 1
    set_coach_calendar_month(year, month)
    if not copy_mode and not delete_mode:
        _sync_selection_to_month(select_key, year, month)


def _programs_on_day(prog_map: dict[str, dict], ds: str) -> list[dict]:
    prog = ensure_program_dict(prog_map.get(ds))
    if not prog:
        return []
    multi = prog.get("_programs")
    if isinstance(multi, list) and multi:
        return [ensure_program_dict(p) for p in multi]
    return [prog]


def _render_coach_program_dialog(ds: str, prog_map: dict[str, dict]) -> None:
    st.markdown(f"### {format_timetable_date(ds)}")
    progs = _programs_on_day(prog_map, ds)
    if not progs:
        st.info("此日無課表（休息）")
        return
    for p in progs:
        tp = safe_str(p.get("type"))
        st.markdown(f"**{short_group_label(p.get('group'))}** · {tp}")
        detail = workout_detail(p)
        if detail:
            st.markdown(detail)
        start, end = safe_str(p.get("start_time")), safe_str(p.get("end_time"))
        time_text = f"{start} – {end}" if start and end else (start or end or "時間待設定")
        st.caption(f"🕐 {time_text} · 📍 {resolve_venue(p)}")
        tips = safe_str(p.get("tips"))
        if tips:
            st.caption(f"備註：{tips}")
        st.markdown("---")


def _coach_compact_day_style(
    ds: str,
    day: int,
    *,
    prog_map: dict[str, dict],
    select_key: str,
    copy_mode: bool,
    delete_mode: bool,
    copy_source: str,
    copy_targets: set,
    delete_targets: set,
    schedule_only: bool = False,
    plan_group: str | None = None,
) -> dict:
    entry = prog_map.get(ds)
    tone = calendar_cell_tone(entry)
    sync_outline = ""
    disabled = False
    pick_label = ""
    chips, extra = calendar_day_event_chips(entry, max_chips=2)

    if copy_mode and ds == copy_source:
        sync_outline = "copy-source"
        pick_label = "源"
    elif copy_mode and ds in copy_targets:
        tone = "picked"
        pick_label = "✓"
    elif delete_mode and ds in delete_targets:
        tone = "picked"
        pick_label = "✓"
    elif delete_mode and ds not in prog_map:
        tone = "disabled"
        disabled = True
        chips, extra = [], 0

    if schedule_only and not copy_mode and not delete_mode:
        if not is_coach_plan_day(entry, plan_group):
            return {
                "tone": "empty",
                "bg": "#f8fafc",
                "sync": "",
                "chips": [],
                "extra_count": 0,
                "disabled": True,
                "pick_label": "",
            }

    if not copy_mode and not delete_mode:
        sync = day_sync_status(entry)
        if sync == "need_workout":
            sync_outline = "workout"
        elif sync == "need_schedule":
            sync_outline = "schedule"
        elif sync == "need_both":
            sync_outline = "both"

    return {
        "tone": tone,
        "bg": calendar_cell_bg(entry),
        "sync": sync_outline,
        "chips": chips,
        "extra_count": extra,
        "disabled": disabled,
        "pick_label": pick_label,
    }


def _coach_pick_for_edit(select_key: str) -> Callable[[str], None]:
    def _pick(ds: str) -> None:
        st.session_state[select_key] = ds
        set_coach_calendar_date(ds)
        st.session_state["coach_prog_screen"] = "edit"

    return _pick


def _render_coach_compact_grid(
    select_key: str,
    year: int,
    month: int,
    prog_map: dict[str, dict],
    copy_mode: bool,
    delete_mode: bool,
    copy_source: str,
    copy_targets: set,
    delete_targets: set,
    *,
    goto_edit_on_select: bool = False,
    schedule_only: bool = False,
    plan_group: str | None = None,
) -> None:
    dialog_key = f"{select_key}_dialog"

    def _style(ds: str, day: int) -> dict:
        return _coach_compact_day_style(
            ds,
            day,
            prog_map=prog_map,
            select_key=select_key,
            copy_mode=copy_mode,
            delete_mode=delete_mode,
            copy_source=copy_source,
            copy_targets=copy_targets,
            delete_targets=delete_targets,
            schedule_only=schedule_only,
            plan_group=plan_group,
        )

    if copy_mode:
        src = copy_source

        def _on_copy_pick(ds: str) -> None:
            _toggle_copy_target(ds, src)

        on_pick = _on_copy_pick
    elif delete_mode:
        valid = set(prog_map.keys())

        def _on_delete_pick(ds: str) -> None:
            if ds in valid:
                _toggle_delete_target(ds)

        on_pick = _on_delete_pick
    elif goto_edit_on_select:
        on_pick = _coach_pick_for_edit(select_key)
    else:
        on_pick = None

    render_timetree_month_grid(
        year=year,
        month=month,
        select_key=select_key,
        dialog_key=dialog_key,
        day_style=_style,
        on_pick=on_pick,
    )

    if not copy_mode and not delete_mode and not goto_edit_on_select:
        open_dialog_if_requested(
            dialog_key,
            lambda ds: _render_coach_program_dialog(ds, prog_map),
            title="課表詳情",
        )


def render_calendar(
    select_key: str = "cal_select",
    show_acwr: bool = False,
    copy_mode: bool = False,
    delete_mode: bool = False,
    group_filter: str | None = None,
    *,
    goto_edit_on_select: bool = False,
    schedule_only: bool = False,
) -> date | None:
    return _render_calendar_impl(
        select_key, show_acwr, copy_mode, delete_mode, group_filter,
        goto_edit_on_select=goto_edit_on_select,
        schedule_only=schedule_only,
    )


def _render_calendar_impl(
    select_key: str,
    show_acwr: bool,
    copy_mode: bool,
    delete_mode: bool,
    group_filter: str | None = None,
    *,
    goto_edit_on_select: bool = False,
    schedule_only: bool = False,
) -> date | None:
    ensure_coach_calendar_state()
    year, month = get_coach_calendar_year_month()

    inject_calendar_theme()

    copy_source = st.session_state.get("copy_source_date", "") if copy_mode else ""
    copy_targets = set(st.session_state.get("copy_target_dates", [])) if copy_mode else set()
    delete_targets = set(st.session_state.get("delete_target_dates", [])) if delete_mode else set()

    render_calendar_month_nav(
        year=year,
        month=month,
        prev_key=f"{select_key}_prev",
        next_key=f"{select_key}_next",
        on_prev=_calendar_prev_month,
        on_next=_calendar_next_month,
        prev_args=(select_key, copy_mode, delete_mode),
        next_args=(select_key, copy_mode, delete_mode),
    )

    if copy_mode:
        st.caption("🟧 橙色=來源 · 🟩 綠色=已選目標（可跨月多選）· 點一下選取/取消")
    elif delete_mode:
        st.caption("🟥 紅色=已選刪除 · 虛線=有課表可選 · 灰底=無課表 · 可跨月多選")
    else:
        render_calendar_legend()
        if schedule_only:
            st.caption("只顯示 **訓練時間表** 已排時間／地點的日子 · 休息日不顯示")

    if not copy_mode and not delete_mode:
        _sync_selection_to_month(select_key, year, month)
    programs = get_programs_for_month(year, month)
    programs = filter_programs_by_group(programs, group_filter)
    prog_map = build_coach_prog_map(programs)

    if select_key not in st.session_state:
        st.session_state[select_key] = st.session_state.get("coach_cal", date.today().isoformat())

    default_mode = "list" if schedule_only else "fullcalendar"
    view_mode = render_view_mode_toggle(
        select_key,
        force_grid=copy_mode or delete_mode,
        default_mode=default_mode,
        variant="program",
    )
    with calendar_shell(key=f"{select_key}_shell"):
        if view_mode == "list":
            athlete_names = get_student_names()
            acwr_athlete = athlete_names[0] if show_acwr and athlete_names else None
            logs = get_all_logs() if show_acwr and acwr_athlete else None

            def _describe(ds: str, prog: dict | None) -> tuple[str, str, str, str]:
                prog = ensure_program_dict(prog)
                tp = safe_str(prog.get("type"))
                sync = day_sync_status(prog_map.get(ds))
                bg = calendar_cell_bg(prog_map.get(ds))
                title_line, spec_line = program_calendar_summary(prog) if prog else ("", "")
                detail = spec_line or ""
                hint = sync_status_label(sync)
                if hint and sync in ("need_workout", "need_schedule", "need_both"):
                    detail = f"{hint} · {detail}".strip(" · ")
                if show_acwr and acwr_athlete and logs is not None:
                    v, _ = acwr_status(calc_acwr(logs, acwr_athlete, date.fromisoformat(ds)))
                    detail = f"{detail} · ACWR {v}".strip(" · ")
                return title_line or "—", detail, tp or "休息", bg

            selected = render_month_day_list(
                year=year,
                month=month,
                select_key=select_key,
                prog_map=prog_map,
                describe_day=_describe,
                pick_mode="copy" if copy_mode else ("delete" if delete_mode else None),
                pick_key="copy_target_dates" if copy_mode else "delete_target_dates",
                copy_source=copy_source,
                empty_label="休息",
                can_pick=(lambda ds, _p: ds in prog_map) if delete_mode else None,
                hide_past_days=not copy_mode and not delete_mode,
                day_priority=lambda ds, p: sync_status_priority(day_sync_status(prog_map.get(ds))),
                goto_edit_on_select=goto_edit_on_select and not copy_mode and not delete_mode,
                day_filter=(
                    (lambda ds, _p: is_coach_plan_day(prog_map.get(ds), group_filter))
                    if schedule_only and not copy_mode and not delete_mode
                    else None
                ),
            )
        elif view_mode == "fullcalendar":
            fc_map = prog_map
            if schedule_only and not copy_mode and not delete_mode:
                fc_map = {
                    ds: p for ds, p in prog_map.items()
                    if is_coach_plan_day(p, group_filter)
                }

            def _fc_title(_ds: str, prog: dict | None) -> str:
                p = ensure_program_dict(prog)
                title_line, spec_line = program_calendar_summary(p) if p else ("", "")
                return title_line or spec_line or "訓練"

            events = build_coach_program_fc_events(fc_map, title_fn=_fc_title)
            render_fullcalendar(
                year=year,
                month=month,
                events=events,
                select_key=select_key,
                fc_key_prefix=f"coach_prog_{select_key}",
                goto_edit_session_key=(
                    "coach_prog_screen"
                    if goto_edit_on_select and not copy_mode and not delete_mode
                    else None
                ),
            )
            selected = date.fromisoformat(st.session_state[select_key])
        else:
            _render_coach_compact_grid(
                select_key, year, month, prog_map,
                copy_mode, delete_mode, copy_source, copy_targets, delete_targets,
                goto_edit_on_select=goto_edit_on_select and not copy_mode and not delete_mode,
                schedule_only=schedule_only and not copy_mode and not delete_mode,
                plan_group=group_filter,
            )
            selected = date.fromisoformat(st.session_state[select_key])

    if copy_mode:
        src_payload = st.session_state.get("copy_source_payload")
        if isinstance(src_payload, list) and src_payload:
            src_title = f"{len(src_payload)} 組課表"
            src_spec = "、".join(short_group_label(p.get("group")) for p in src_payload[:4])
        else:
            src_prog = ensure_program_dict(src_payload)
            src_title, src_spec = program_calendar_summary(src_prog) if src_prog else ("", "")
        targets = st.session_state.get("copy_target_dates", [])
        target_text = "、".join(targets) if targets else "（尚未選擇）"
        st.warning(
            f"📋 **複製模式** — 來源：**{copy_source}** {src_title} {src_spec}\n\n"
            f"👉 在月曆上**點選多個目標日期**（可切換月份），再按「確認複製」\n\n"
            f"已選 **{len(targets)}** 日：{target_text}"
        )
    elif delete_mode:
        targets = st.session_state.get("delete_target_dates", [])
        target_text = "、".join(targets) if targets else "（尚未選擇）"
        st.error(
            f"🗑 **多選刪除模式** — 在月曆上點選**有課表的日期**（可跨月），再按「確認刪除」\n\n"
            f"已選 **{len(targets)}** 日：{target_text}"
        )
    else:
        hint = (
            f"已選日期：**{st.session_state[select_key]}** · 點選日期直接編輯課表"
            if goto_edit_on_select
            else f"已選日期：**{st.session_state[select_key]}** · 格內色條=課表摘要 · 點格查看詳情"
        )
        st.caption(hint)
    set_coach_calendar_date(str(st.session_state[select_key]))
    return selected
