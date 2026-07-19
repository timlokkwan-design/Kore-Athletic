"""Coach — recent same-group workout history for side-by-side comparison."""

from __future__ import annotations

import html
from datetime import date, timedelta

import streamlit as st

from utils.config import GROUP_OPTIONS, WEEKDAY_SHORT, group_display_label, normalize_group, normalize_train_type
from utils.data_store import get_group_training_history
from utils.helpers import (
    format_meters_short,
    format_time_venue_line,
    format_timetable_date,
    safe_str,
    workout_detail,
    workout_volume_from_program,
)

_COMPARE_GROUPS = [g for g in GROUP_OPTIONS if g != "全體組員"]
_DIALOG_KEY = "coach_hist_dialog_pick"


def _date_heading(prog: dict) -> str:
    ds = safe_str(prog.get("date"))
    try:
        d = date.fromisoformat(ds)
        return f"{d.month}/{d.day}（{WEEKDAY_SHORT[d.weekday()]}）"
    except ValueError:
        return ds


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


def _render_history_entry(
    prog: dict,
    group: str,
    *,
    key_suffix: str,
) -> None:
    ds = safe_str(prog.get("date"))
    heading = _date_heading(prog)
    vol = _vol_label(prog)
    tp = normalize_train_type(safe_str(prog.get("type")))
    detail = workout_detail(prog) or "（無跑案內容）"
    vol_text = f" · {vol}" if vol else ""
    type_text = f" · {tp}" if tp == "比賽" else ""

    from views.components.theme import get_ui_colors

    uc = get_ui_colors()
    st.markdown(
        f"<div style='background:{uc['card_bg']};border:1px solid {uc['border']};border-radius:8px;"
        f"padding:8px 10px 4px;margin-bottom:4px;'>"
        f"<div style='font-size:12px;font-weight:700;color:{uc['text']};'>"
        f"{html.escape(heading)}{html.escape(vol_text)}{html.escape(type_text)}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<pre style='white-space:pre-wrap;word-break:break-word;font-family:inherit;"
        f"font-size:12px;line-height:1.45;color:{uc['text']};background:{uc['card_bg']};"
        f"border:1px solid {uc['border']};border-top:none;border-radius:0 0 8px 8px;"
        f"padding:8px 10px;margin:0 0 6px;max-height:180px;overflow-y:auto;'>"
        f"{html.escape(detail)}</pre>",
        unsafe_allow_html=True,
    )
    st.button(
        "🔍 放大檢視",
        key=f"hist_zoom_{key_suffix}_{ds}",
        use_container_width=True,
        on_click=_pick_history_entry,
        args=(prog, group),
    )


def _range_caption(selected: date, group: str, days_back: int, count: int) -> str:
    start = selected - timedelta(days=days_back)
    end = selected - timedelta(days=1)
    gl = group_display_label(group)
    sel = format_timetable_date(selected.isoformat())
    if count == 0:
        return (
            f"選定日 **{sel}** · **{gl}** 在 {start.month}/{start.day}–"
            f"{end.month}/{end.day}（不含選定日）無訓練紀錄"
        )
    return (
        f"選定日 **{sel}** · 顯示 **{gl}** 在 {start.month}/{start.day}–"
        f"{end.month}/{end.day}（不含選定日）共 **{count}** 次訓練 · 按 **放大檢視** 全屏閱讀"
    )


def render_workout_history_compare(
    selected: date,
    *,
    highlight_group: str | None = None,
    groups: list[str] | None = None,
    days_back: int = 14,
    show_heading: bool = True,
) -> None:
    """
    List training days for the editing group only — dates in (selected - 14d, selected).
    """
    show_groups = groups or _COMPARE_GROUPS
    if highlight_group:
        hg = normalize_group(highlight_group)
        show_groups = [g for g in show_groups if normalize_group(g) == hg] or [hg]

    for col_idx, grp in enumerate(show_groups):
        history = get_group_training_history(selected, grp, days_back=days_back)
        gl = group_display_label(grp)

        if show_heading:
            st.markdown(f"**📊 近2週 · {gl} 跑案參考**")
            st.caption(_range_caption(selected, grp, days_back, len(history)))

        if len(show_groups) > 1:
            st.markdown(f"**{gl}**")

        if not history:
            if not show_heading:
                st.caption(_range_caption(selected, grp, days_back, 0))
            continue

        grp_key = normalize_group(grp).replace(" ", "")
        for i, prog in enumerate(history):
            _render_history_entry(
                prog,
                grp,
                key_suffix=f"g{col_idx}_{grp_key}_{i}_{selected.isoformat()}",
            )

    _open_history_dialog()
