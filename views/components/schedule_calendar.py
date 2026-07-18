"""Month calendar for coach training timetable (time & venue)."""

import calendar
from datetime import date

import streamlit as st

from utils.config import TRAIN_TYPES, TYPE_CATEGORY_COLORS, normalize_train_type
from utils.data_store import get_programs_for_month, is_training_day, has_schedule_slot, build_coach_prog_map
from utils.helpers import (
    day_sync_status,
    format_timetable_date,
    normalize_date_str,
    program_calendar_summary,
    resolve_venue,
    safe_str,
    sync_status_label,
    sync_status_priority,
    format_time_venue_line,
)
from views.components.calendar_compact import open_dialog_if_requested, render_compact_month_grid
from views.components.calendar_list import render_month_day_list, render_view_mode_toggle


def _sync_sched_month(select_key: str, year: int, month: int) -> None:
    cur = st.session_state.get(select_key, date.today().isoformat())
    try:
        sel = date.fromisoformat(str(cur))
    except ValueError:
        sel = date.today()
    if sel.year == year and sel.month == month:
        return
    today = date.today()
    if today.year == year and today.month == month:
        st.session_state[select_key] = today.isoformat()
    else:
        st.session_state[select_key] = f"{year}-{month:02d}-01"


def _toggle_pick(ds: str, pick_key: str, source: str = "", *, block_source: bool = False) -> None:
    if block_source and ds == source:
        st.session_state["sched_flash"] = ("error", "來源日期不能選為目標")
        return
    picks = list(st.session_state.get(pick_key, []))
    if ds in picks:
        picks.remove(ds)
    else:
        picks.append(ds)
    st.session_state[pick_key] = sorted(picks)


def _sched_pick_day(ds: str, pick_key: str, copy_source: str, pick_mode: str | None) -> None:
    if pick_mode:
        _toggle_pick(ds, pick_key, copy_source, block_source=(pick_mode == "copy"))


def _sched_prev_month(select_key: str, pick_mode: str | None) -> None:
    if st.session_state.sched_cal_month == 1:
        st.session_state.sched_cal_month, st.session_state.sched_cal_year = 12, st.session_state.sched_cal_year - 1
    else:
        st.session_state.sched_cal_month -= 1
    if not pick_mode:
        _sync_sched_month(select_key, st.session_state.sched_cal_year, st.session_state.sched_cal_month)


def _sched_next_month(select_key: str, pick_mode: str | None) -> None:
    if st.session_state.sched_cal_month == 12:
        st.session_state.sched_cal_month, st.session_state.sched_cal_year = 1, st.session_state.sched_cal_year + 1
    else:
        st.session_state.sched_cal_month += 1
    if not pick_mode:
        _sync_sched_month(select_key, st.session_state.sched_cal_year, st.session_state.sched_cal_month)


def _cell_summary(prog: dict | None) -> tuple[str, str, str]:
    """Return (title_line, detail_line, train_type) for calendar cell."""
    if not prog:
        return "可預排", "點選後設定時間地點", "—"
    tp = normalize_train_type(safe_str(prog.get("type")))
    if tp == "休息":
        return "休息", "", "休息"
    sync = day_sync_status(prog)
    title, spec = program_calendar_summary(prog)
    time_line = format_time_venue_line(prog)
    detail_parts = []
    hint = sync_status_label(sync)
    if hint and sync in ("need_workout", "need_schedule", "need_both"):
        detail_parts.append(hint)
    if time_line:
        detail_parts.append(time_line)
    elif spec:
        detail_parts.append(spec)
    detail = " · ".join(detail_parts)
    if tp == "待排課":
        return title or "待寫跑案", detail, tp
    return title or tp, detail, tp


def _render_sched_day_dialog(ds: str, prog_map: dict[str, dict]) -> None:
    st.markdown(f"### {format_timetable_date(ds)}")
    prog = prog_map.get(ds)
    sync = day_sync_status(prog)
    if not prog:
        st.info("此日尚未排課，可直接在下方預先設定時間與地點。")
        return
    if sync == "rest":
        st.info("此日為休息。")
        return
    title, detail, tp = _cell_summary(prog)
    hint = sync_status_label(sync)
    if hint:
        st.caption(hint)
    st.markdown(f"**{title}**")
    if detail:
        st.caption(detail)
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    time_text = f"{start} – {end}" if start and end else (start or end or "時間待設定")
    st.markdown(f"🕐 **{time_text}**")
    st.markdown(f"📍 **{resolve_venue(prog)}**")
    from utils.helpers import workout_detail

    wdetail = workout_detail(prog)
    if wdetail:
        st.markdown("**跑案**")
        st.markdown(wdetail)
    elif sync == "need_workout":
        st.warning("請至「週期化課表」填寫跑案內容。")
    elif sync == "need_schedule":
        st.warning("請在此頁設定訓練時間與地點。")


def _sched_compact_style(
    ds: str,
    day: int,
    *,
    prog_map: dict[str, dict],
    select_key: str,
    pick_mode: str | None,
    copy_source: str,
    picks: set,
) -> dict:
    today_str = date.today().isoformat()
    prog = prog_map.get(ds)
    title, detail, tp = _cell_summary(prog)
    sync = day_sync_status(prog)
    if sync == "need_workout":
        cat = "pending"
    elif sync == "need_schedule":
        cat = TRAIN_TYPES.get(tp, {}).get("category", "rest")
    elif tp == "—":
        cat = "rest"
    else:
        cat = TRAIN_TYPES.get(tp, {}).get("category", "rest")
    bg = TYPE_CATEGORY_COLORS.get(cat, "#f1f5f9")
    border = "1px solid #e2e8f0"
    label = f"●{day}" if ds == today_str else str(day)
    disabled = False

    if pick_mode == "copy" and ds == copy_source:
        border = "3px solid #f59e0b"
    elif pick_mode and ds in picks:
        border = "3px solid #16a34a"
        bg = "#dcfce7"
        label = f"✓{day}"
    elif pick_mode == "copy" and ds != copy_source:
        label = f"+{day}"
    elif pick_mode:
        label = f"+{day}" if ds not in picks else f"✓{day}"
    elif st.session_state.get(select_key) == ds:
        border = "2px solid #1d4ed8"

    if not pick_mode:
        if sync == "need_workout":
            bg = "#fef3c7"
            border = "2px solid #f59e0b"
        elif sync == "need_schedule":
            border = "2px solid #ea580c"
        time_hint = format_time_venue_line(prog) if prog else ""
        if time_hint and len(time_hint) <= 10:
            label = f"{day}·{time_hint[:8]}"

    hint = ""
    if not pick_mode and prog and format_time_venue_line(prog):
        hint = format_time_venue_line(prog)[:12]

    return {"bg": bg, "border": border, "label": label, "disabled": disabled, "hint": hint}


def _render_sched_compact_grid(
    select_key: str,
    year: int,
    month: int,
    prog_map: dict[str, dict],
    pick_mode: str | None,
    pick_key: str,
    copy_source: str,
    picks: set,
) -> None:
    dialog_key = f"{select_key}_dialog"

    def _style(ds: str, day: int) -> dict:
        return _sched_compact_style(
            ds, day,
            prog_map=prog_map,
            select_key=select_key,
            pick_mode=pick_mode,
            copy_source=copy_source,
            picks=picks,
        )

    if pick_mode:

        def _on_pick(ds: str) -> None:
            _sched_pick_day(ds, pick_key, copy_source, pick_mode)

        on_pick = _on_pick
    else:
        on_pick = None

    render_compact_month_grid(
        year=year,
        month=month,
        select_key=select_key,
        dialog_key=dialog_key,
        day_style=_style,
        on_pick=on_pick,
    )

    if not pick_mode:
        open_dialog_if_requested(
            dialog_key,
            lambda ds: _render_sched_day_dialog(ds, prog_map),
            title="訓練時間表",
        )


def render_schedule_calendar(
    select_key: str = "sched_cal",
    *,
    pick_mode: str | None = None,
    pick_key: str = "sched_pick_dates",
    copy_source: str = "",
) -> date:
    """
    pick_mode: None | 'copy' | 'bulk'
    """
    if "sched_cal_year" not in st.session_state:
        t = date.today()
        st.session_state.sched_cal_year, st.session_state.sched_cal_month = t.year, t.month

    picks = set(st.session_state.get(pick_key, []))

    c1, c2, c3 = st.columns([1, 2, 1])
    c1.button(
        "◀ 上月",
        key=f"{select_key}_prev",
        on_click=_sched_prev_month,
        args=(select_key, pick_mode),
    )
    c2.markdown(f"### {st.session_state.sched_cal_year} 年 {st.session_state.sched_cal_month:02d} 月")
    c3.button(
        "下月 ▶",
        key=f"{select_key}_next",
        on_click=_sched_next_month,
        args=(select_key, pick_mode),
    )

    if pick_mode == "copy":
        st.caption("🟧 橙色=來源 · 🟩 綠色=已選目標 · 可選任意日期")
    elif pick_mode == "bulk":
        st.caption("🟩 綠色=已選 · 可選任意日期預排時間地點")
    else:
        st.caption("🟨 黃色=時間已定待寫跑案 · 🟧 框線=待填時間 · 可預先排定任意日期")

    year, month = st.session_state.sched_cal_year, st.session_state.sched_cal_month
    if not pick_mode:
        _sync_sched_month(select_key, year, month)

    programs = get_programs_for_month(year, month)
    prog_map = build_coach_prog_map(programs)

    if select_key not in st.session_state:
        st.session_state[select_key] = date.today().isoformat()

    view_mode = render_view_mode_toggle(select_key)

    def _describe(ds: str, prog: dict | None) -> tuple[str, str, str, str]:
        title_line, detail_line, tp = _cell_summary(prog)
        cat = TRAIN_TYPES.get(tp, {}).get("category", "rest")
        bg = TYPE_CATEGORY_COLORS.get(cat, "#f1f5f9")
        return title_line, detail_line, tp, bg

    if view_mode == "list":
        selected = render_month_day_list(
            year=year,
            month=month,
            select_key=select_key,
            prog_map=prog_map,
            describe_day=_describe,
            pick_mode=pick_mode,
            pick_key=pick_key,
            copy_source=copy_source,
            empty_label="可預排",
            can_pick=(lambda _ds, _p: True) if pick_mode else None,
            day_priority=lambda ds, p: sync_status_priority(day_sync_status(prog_map.get(ds))),
        )
    else:
        _render_sched_compact_grid(
            select_key, year, month, prog_map, pick_mode, pick_key, copy_source, picks
        )
        selected = date.fromisoformat(st.session_state[select_key])

    picks_list = st.session_state.get(pick_key, [])

    if pick_mode == "copy":
        src_prog = prog_map.get(copy_source) or {}
        src_title, _, _ = _cell_summary(src_prog)
        st.warning(
            f"📋 **複製時間地點** — 來源：**{copy_source}** {src_title}\n\n"
            f"👉 多選訓練日後按「確認複製」\n\n"
            f"已選 **{len(picks_list)}** 日：{('、'.join(picks_list) if picks_list else '（尚未選擇）')}"
        )
    elif pick_mode == "bulk":
        st.warning(
            f"✅ **多選套用** — 已選 **{len(picks_list)}** 日："
            f"{('、'.join(picks_list) if picks_list else '（請在月曆點選訓練日）')}"
        )
    else:
        st.caption(f"已選日期：**{st.session_state[select_key]}** · 點方格可彈出詳情")

    return selected
