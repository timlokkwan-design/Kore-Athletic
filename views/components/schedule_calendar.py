"""Month calendar for coach training timetable (time & venue)."""

import calendar
from datetime import date

import streamlit as st

from utils.config import normalize_train_type
from utils.data_store import get_programs_for_month, build_day_programs_map
from utils.helpers import (
    calendar_cell_bg,
    day_sync_status,
    format_timetable_date,
    normalize_date_str,
    program_sync_status,
    resolve_venue,
    safe_str,
    short_group_label,
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


def _normalize_progs(progs: list[dict] | dict | None) -> list[dict]:
    if progs is None:
        return []
    if isinstance(progs, dict):
        if progs.get("_programs"):
            return list(progs["_programs"])
        return [progs]
    return list(progs)


def _merged_for_sync(progs: list[dict]) -> dict | None:
    if not progs:
        return None
    if len(progs) == 1:
        return progs[0]
    merged = dict(progs[0])
    merged["_programs"] = progs
    return merged


def _cell_summary(progs: list[dict] | dict | None) -> tuple[str, str, str]:
    """Return (title_line, detail_line, train_type) for calendar cell."""
    progs = _normalize_progs(progs)
    if not progs:
        return "可預排", "", "—"
    active = [
        p for p in progs
        if normalize_train_type(safe_str(p.get("type"))) not in ("休息",)
    ]
    if not active:
        return "休息", "", "休息"
    parts: list[str] = []
    for p in active:
        gl = short_group_label(p.get("group"))
        tv = format_time_venue_line(p)
        if tv:
            parts.append(f"{gl} {tv}")
        else:
            parts.append(gl)
    title = f"{len(active)}組" if len(active) > 1 else short_group_label(active[0].get("group"))
    detail = " · ".join(parts[:3])
    tp = normalize_train_type(safe_str(active[0].get("type")))
    return title, detail, tp


def _render_sched_day_dialog(ds: str, day_map: dict[str, list[dict]]) -> None:
    st.markdown(f"### {format_timetable_date(ds)}")
    progs = day_map.get(ds, [])
    if not progs:
        st.info("此日尚未排課，可為各組別預先設定時間與地點。")
        return
    for p in progs:
        tp = normalize_train_type(safe_str(p.get("type")))
        if tp == "休息":
            continue
        gl = short_group_label(p.get("group"))
        st.markdown(f"**{gl}**")
        hint = sync_status_label(program_sync_status(p))
        if hint:
            st.caption(hint)
        start = safe_str(p.get("start_time"))
        end = safe_str(p.get("end_time"))
        time_text = f"{start} – {end}" if start and end else (start or end or "時間待設定")
        st.markdown(f"🕐 {time_text} · 📍 {resolve_venue(p)}")
        from utils.helpers import workout_detail

        wdetail = workout_detail(p)
        if wdetail:
            st.markdown(wdetail)
        st.markdown("---")


def _sched_compact_style(
    ds: str,
    day: int,
    *,
    day_map: dict[str, list[dict]],
    select_key: str,
    pick_mode: str | None,
    copy_source: str,
    picks: set,
) -> dict:
    today_str = date.today().isoformat()
    progs = day_map.get(ds, [])
    title, detail, tp = _cell_summary(progs)
    sync = day_sync_status(_merged_for_sync(progs))
    bg = calendar_cell_bg(progs=progs)
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
            border = "2px solid #f59e0b"
        elif sync == "need_schedule":
            border = "2px solid #ea580c"
        elif sync == "need_both":
            border = "2px dashed #f59e0b"
        if len(progs) == 1:
            time_hint = format_time_venue_line(progs[0])
            if time_hint and len(time_hint) <= 10:
                label = f"{day}·{time_hint[:8]}"
        elif len(progs) > 1:
            label = f"{day}·{len(progs)}組"

    hint = detail[:24] if detail and not pick_mode else ""

    return {"bg": bg, "border": border, "label": label, "disabled": disabled, "hint": hint}


def _render_sched_compact_grid(
    select_key: str,
    year: int,
    month: int,
    day_map: dict[str, list[dict]],
    pick_mode: str | None,
    pick_key: str,
    copy_source: str,
    picks: set,
) -> None:
    dialog_key = f"{select_key}_dialog"

    def _style(ds: str, day: int) -> dict:
        return _sched_compact_style(
            ds, day,
            day_map=day_map,
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
            lambda ds: _render_sched_day_dialog(ds, day_map),
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
        st.caption("🔵 藍色=訓練 · 🔴 紅色=比賽 · 🟨 框線=待同步 · 可預先排定任意日期")

    year, month = st.session_state.sched_cal_year, st.session_state.sched_cal_month
    if not pick_mode:
        _sync_sched_month(select_key, year, month)

    programs = get_programs_for_month(year, month)
    day_map = build_day_programs_map(programs)
    prog_map = {
        ds: _merged_for_sync(progs) for ds, progs in day_map.items()
    }

    if select_key not in st.session_state:
        st.session_state[select_key] = date.today().isoformat()

    view_mode = render_view_mode_toggle(select_key)

    def _describe(ds: str, prog: dict | None) -> tuple[str, str, str, str]:
        progs = day_map.get(ds, [])
        title_line, detail_line, tp = _cell_summary(progs)
        bg = calendar_cell_bg(progs=progs)
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
            select_key, year, month, day_map, pick_mode, pick_key, copy_source, picks
        )
        selected = date.fromisoformat(st.session_state[select_key])

    picks_list = st.session_state.get(pick_key, [])

    if pick_mode == "copy":
        src_title, _, _ = _cell_summary(day_map.get(copy_source, []))
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
