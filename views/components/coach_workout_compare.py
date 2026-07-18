"""Coach — recent same-group workout history as 7-column square grid."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from utils.config import GROUP_OPTIONS, group_display_label, normalize_group, normalize_train_type
from utils.data_store import get_programs_for_date
from utils.helpers import (
    calendar_cell_tone,
    format_meters_short,
    format_time_venue_line,
    format_timetable_date,
    safe_str,
    workout_detail,
    workout_volume_from_program,
)
from views.components.calendar_compact import (
    SquareCell,
    inject_compact_calendar_css,
    render_seven_column_row,
)

_COMPARE_GROUPS = [g for g in GROUP_OPTIONS if g != "全體組員"]
_DIALOG_KEY = "coach_hist_dialog_pick"


def _vol_label(prog: dict) -> str:
    vol = format_meters_short(workout_volume_from_program(prog)["total_meters"])
    return vol or ""


def _open_history_dialog() -> None:
    pick = st.session_state.pop(_DIALOG_KEY, None)
    if not pick or not isinstance(pick, dict):
        return
    prog = pick.get("prog") or {}
    group = group_display_label(pick.get("group"))
    ds = safe_str(prog.get("date"))
    title = f"{group} · {format_timetable_date(ds) if ds else '跑案'}"

    @st.dialog(title, width="large")
    def _popup() -> None:
        tp = normalize_train_type(safe_str(prog.get("type")))
        st.markdown(f"**組別：** {group} · **類型：** {tp}")
        vol = _vol_label(prog)
        if vol:
            st.markdown(f"**總跑量：** {vol}")
        tv = format_time_venue_line(prog)
        if tv:
            st.caption(f"🕐 {tv}")
        detail = workout_detail(prog)
        st.markdown("**跑案內容**")
        if detail:
            st.markdown(detail)
        else:
            st.info("此日無跑案文字")
        tips = safe_str(prog.get("tips"))
        if tips:
            st.markdown("**教練備註**")
            st.markdown(tips)
        rpe = safe_str(prog.get("rpe"))
        if rpe and rpe not in ("0", "nan", "None"):
            st.caption(f"RPE {rpe}")

    _popup()


def _pick_history_entry(prog: dict, group: str) -> None:
    st.session_state[_DIALOG_KEY] = {"prog": dict(prog), "group": group}


def _prog_for_group_on_date(d: date, group: str) -> dict | None:
    target = normalize_group(group)
    for p in get_programs_for_date(d):
        if normalize_group(safe_str(p.get("group"))) == target:
            tp = normalize_train_type(safe_str(p.get("type")))
            if tp == "休息":
                return None
            return p
    return None


def _past_days(anchor: date, days_back: int) -> list[date]:
    return [anchor - timedelta(days=i) for i in range(days_back, 0, -1)]


def _render_history_grid(
    selected: date,
    group: str,
    *,
    days_back: int = 14,
    key_prefix: str,
) -> None:
    """Two rows × 7 cols = past 14 days; tap square to enlarge."""
    days = _past_days(selected, days_back)
    inject_compact_calendar_css()
    st.markdown('<div class="ka-cal-7grid ka-hist-grid">', unsafe_allow_html=True)

    grp_key = normalize_group(group).replace(" ", "")

    for row_idx in range(2):
        chunk = days[row_idx * 7 : (row_idx + 1) * 7]
        cells: list[SquareCell] = []
        for d in chunk:
            ds = d.isoformat()
            prog = _prog_for_group_on_date(d, group)
            tone = calendar_cell_tone(prog) if prog else "empty"
            if tone == "rest":
                tone = "empty"
            label = str(d.day)
            if prog:
                vol = _vol_label(prog)
                tp = normalize_train_type(safe_str(prog.get("type")))
                if tp == "比賽":
                    label = f"{d.day}賽"
                elif vol:
                    label = f"{d.day}·{vol[:3]}"
            cells.append(
                SquareCell(
                    key_id=ds,
                    label=label,
                    tone=tone,
                    disabled=prog is None,
                )
            )
        render_seven_column_row(
            cells,
            key_prefix=f"{key_prefix}_{grp_key}",
            row_idx=row_idx,
            on_click=_pick_history_entry,
            click_args_fn=lambda cell, g=group: (
                _prog_for_group_on_date(date.fromisoformat(cell.key_id), g) or {"date": cell.key_id},
                g,
            ),
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("點藍/紅方格放大檢視跑案 · 灰格為該日無此組訓練")


def render_workout_history_compare(
    selected: date,
    *,
    highlight_group: str | None = None,
    groups: list[str] | None = None,
    days_back: int = 14,
    show_heading: bool = True,
) -> None:
    """Past training plans as 7-column square grids; tap to open full detail."""
    show_groups = groups or _COMPARE_GROUPS
    if highlight_group:
        hg = normalize_group(highlight_group)
        if groups is None:
            ordered = [hg] + [g for g in show_groups if normalize_group(g) != hg]
            show_groups = ordered
        else:
            show_groups = [g for g in show_groups if normalize_group(g) == hg] or [hg]

    if show_heading:
        if len(show_groups) == 1:
            gl = group_display_label(show_groups[0])
            st.markdown(f"#### 📊 近2週 · {gl} 跑案參考")
        else:
            st.markdown("#### 📊 近2週同組別跑案參考")
        st.caption(f"選定日 **{selected.month}/{selected.day}** · 7 格一列 · 點方格放大")

    for gi, grp in enumerate(show_groups):
        if len(show_groups) > 1:
            st.markdown(f"**{group_display_label(grp)}**")
        _render_history_grid(
            selected,
            grp,
            days_back=days_back,
            key_prefix=f"hist_{gi}",
        )

    _open_history_dialog()
