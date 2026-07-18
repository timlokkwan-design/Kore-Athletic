"""Coach — recent same-group workout history for side-by-side comparison."""

from __future__ import annotations

import html
from datetime import date

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
    highlight: bool,
    key_suffix: str,
) -> None:
    ds = safe_str(prog.get("date"))
    heading = _date_heading(prog)
    vol = _vol_label(prog)
    tp = normalize_train_type(safe_str(prog.get("type")))
    detail = workout_detail(prog) or "（無跑案內容）"
    border = "#1d4ed8" if highlight else "#cbd5e1"
    bg = "#eff6ff" if highlight else "#f8fafc"
    vol_text = f" · {vol}" if vol else ""
    type_text = f" · {tp}" if tp == "比賽" else ""

    st.markdown(
        f"<div style='background:{bg};border:1px solid {border};border-radius:8px;"
        f"padding:8px 10px 4px;margin-bottom:4px;'>"
        f"<div style='font-size:12px;font-weight:700;color:#1e3a8a;'>"
        f"{html.escape(heading)}{html.escape(vol_text)}{html.escape(type_text)}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<pre style='white-space:pre-wrap;word-break:break-word;font-family:inherit;"
        f"font-size:12px;line-height:1.45;color:#334155;background:{bg};"
        f"border:1px solid {border};border-top:none;border-radius:0 0 8px 8px;"
        f"padding:8px 10px;margin:0 0 6px;max-height:220px;overflow-y:auto;'>"
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


def _render_group_column(
    selected: date,
    group: str,
    *,
    highlight: bool,
    col_idx: int,
    days_back: int = 14,
) -> None:
    label = group_display_label(group)
    history = get_group_training_history(selected, group, days_back=days_back)
    if highlight:
        st.markdown(f"**🔹 {label}**")
    else:
        st.markdown(f"**{label}**")
    if not history:
        st.caption("近2週無訓練紀錄")
        return
    grp_key = normalize_group(group).replace(" ", "")
    for i, prog in enumerate(history):
        _render_history_entry(
            prog,
            group,
            highlight=highlight,
            key_suffix=f"g{col_idx}_{grp_key}_{i}",
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
    Show past training plans for given group(s).
    Full workout text inline; tap 放大檢視 for dialog.
    """
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
        st.caption(
            f"選定日 **{selected.month}/{selected.day}** · "
            f"完整跑案可直接對照 · 按 **放大檢視** 可全屏閱讀"
        )

    n = len(show_groups)
    if n == 1:
        _render_group_column(
            selected,
            show_groups[0],
            highlight=True,
            col_idx=0,
            days_back=days_back,
        )
    else:
        cols = st.columns(n)
        for col_idx, (col, grp) in enumerate(zip(cols, show_groups)):
            with col:
                _render_group_column(
                    selected,
                    grp,
                    highlight=highlight_group is not None and normalize_group(grp) == normalize_group(highlight_group),
                    col_idx=col_idx,
                    days_back=days_back,
                )

    _open_history_dialog()
