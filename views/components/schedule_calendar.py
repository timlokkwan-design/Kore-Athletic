"""Month calendar for coach training timetable (time & venue)."""

import calendar
from datetime import date

import streamlit as st

from utils.config import TRAIN_TYPES, TYPE_CATEGORY_COLORS, normalize_train_type
from utils.data_store import get_programs_for_month, is_training_day, build_coach_prog_map
from utils.helpers import format_timetable_date, normalize_date_str, program_calendar_summary, resolve_venue, safe_str
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
    if pick_mode and is_training_day(ds):
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
        return "休息", "", "休息"
    tp = normalize_train_type(safe_str(prog.get("type")))
    if tp == "休息":
        return "休息", "", "休息"
    title, spec = program_calendar_summary(prog)
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    time_part = f"{start}–{end}" if start and end else (start or end or "")
    venue = resolve_venue(prog)
    if venue == "（待設定）":
        venue = ""
    parts = [p for p in (time_part, venue) if p]
    detail = " · ".join(parts)
    return title or tp, detail, tp


def _render_sched_day_dialog(ds: str, prog_map: dict[str, dict]) -> None:
    st.markdown(f"### {format_timetable_date(ds)}")
    prog = prog_map.get(ds)
    if not prog or not is_training_day(ds):
        st.info("此日為休息，無時間地點設定。")
        return
    title, detail, tp = _cell_summary(prog)
    st.markdown(f"**{tp}** · {title}")
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    time_text = f"{start} – {end}" if start and end else (start or end or "時間待設定")
    st.markdown(f"🕐 **{time_text}**")
    st.markdown(f"📍 **{resolve_venue(prog)}**")
    if detail:
        st.caption(detail)


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
    title, _, tp = _cell_summary(prog)
    cat = TRAIN_TYPES.get(tp, {}).get("category", "rest")
    bg = TYPE_CATEGORY_COLORS.get(cat, "#f1f5f9")
    border = "1px solid #e2e8f0"
    label = f"●{day}" if ds == today_str else str(day)
    disabled = False
    training = is_training_day(ds)

    if pick_mode == "copy" and ds == copy_source:
        border = "3px solid #f59e0b"
    elif pick_mode and ds in picks:
        border = "3px solid #16a34a"
        bg = "#dcfce7"
        label = f"✓{day}"
    elif pick_mode == "copy" and ds != copy_source and training:
        label = f"+{day}"
    elif pick_mode and training:
        label = f"+{day}" if ds not in picks else f"✓{day}"
    elif pick_mode and not training:
        disabled = True
        bg = "#f8fafc"
    elif st.session_state.get(select_key) == ds:
        border = "2px solid #1d4ed8"

    return {"bg": bg, "border": border, "label": label, "disabled": disabled}


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
        st.caption("🟧 橙色=來源 · 🟩 綠色=已選目標 · 僅訓練日可複製")
    elif pick_mode == "bulk":
        st.caption("🟩 綠色=已選 · 點一下選取/取消 · 僅訓練日可套用")
    else:
        st.caption("有課表=訓練日 · 點日期方格查看時間地點")

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
            empty_label="休息",
            can_pick=(lambda ds, _p: is_training_day(ds)) if pick_mode else None,
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
