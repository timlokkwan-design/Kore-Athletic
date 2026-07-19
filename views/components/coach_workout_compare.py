"""Coach — recent same-group workout history for side-by-side comparison."""

from __future__ import annotations

import html
from collections.abc import Callable
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


def _inject_hist_row_css() -> None:
    st.markdown(
        """
        <style>
        /* Scoped: only the block that directly owns the hist-actions marker */
        [data-testid="stVerticalBlock"]:has(> div .ka-hist-actions-marker) > [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.35rem !important;
            width: 100% !important;
        }
        [data-testid="stVerticalBlock"]:has(> div .ka-hist-actions-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 0 !important;
            flex: 1 1 0 !important;
        }
        [data-testid="stVerticalBlock"]:has(> div .ka-hist-actions-marker) > [data-testid="stHorizontalBlock"] button {
            min-height: 2.5rem !important;
            font-weight: 700 !important;
            font-size: clamp(0.72rem, 3.2vw, 0.9rem) !important;
            white-space: nowrap !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_history_entry(
    prog: dict,
    group: str,
    *,
    key_suffix: str,
    on_copy_program: Callable[[dict], None] | None = None,
    show_week_copy: bool = False,
    on_copy_week: Callable[[], None] | None = None,
    copy_week_key: str | None = None,
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

    with st.container():
        st.markdown(
            '<div class="ka-hist-actions-marker" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.button(
                "🔍 放大",
                key=f"hist_zoom_{key_suffix}_{ds}",
                use_container_width=True,
                on_click=_pick_history_entry,
                args=(prog, group),
            )
        with c2:
            if show_week_copy and on_copy_week and copy_week_key:
                if st.button(
                    "📋 複製上週",
                    key=copy_week_key,
                    use_container_width=True,
                    help="帶入 7 天前同一星期幾的跑案、備註與 RPE",
                ):
                    on_copy_week()
                    st.rerun()
            elif on_copy_program:
                if st.button(
                    "📋 複製",
                    key=f"hist_copy_{key_suffix}_{ds}",
                    use_container_width=True,
                    help="帶入此日跑案到編輯區",
                ):
                    on_copy_program(prog)
                    st.rerun()
            else:
                st.button(
                    "📋 複製",
                    key=f"hist_copy_disabled_{key_suffix}_{ds}",
                    use_container_width=True,
                    disabled=True,
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
        f"{end.month}/{end.day}（不含選定日）共 **{count}** 次訓練"
    )


def render_workout_history_compare(
    selected: date,
    *,
    highlight_group: str | None = None,
    groups: list[str] | None = None,
    days_back: int = 14,
    show_heading: bool = True,
    on_copy_week: Callable[[], None] | None = None,
    copy_week_key: str | None = None,
    on_copy_program: Callable[[dict], None] | None = None,
) -> None:
    """
    List training days for the editing group only — dates in (selected - 14d, selected).
    """
    _inject_hist_row_css()
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
            if on_copy_week and copy_week_key:
                if st.button(
                    "📋 複製上週同天",
                    key=copy_week_key,
                    use_container_width=True,
                    help="帶入 7 天前同一星期幾的跑案、備註與 RPE",
                ):
                    on_copy_week()
                    st.rerun()
            continue

        grp_key = normalize_group(grp).replace(" ", "")
        for i, prog in enumerate(history):
            _render_history_entry(
                prog,
                grp,
                key_suffix=f"g{col_idx}_{grp_key}_{i}_{selected.isoformat()}",
                on_copy_program=on_copy_program,
                show_week_copy=(i == 0 and on_copy_week is not None),
                on_copy_week=on_copy_week,
                copy_week_key=copy_week_key if i == 0 else None,
            )

    _open_history_dialog()
