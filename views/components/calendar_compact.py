"""Compact 7-column month grid for mobile — small cells, dialog on tap."""
from __future__ import annotations

import calendar
from datetime import date
from typing import Callable

import streamlit as st


def inject_compact_calendar_css() -> None:
    st.markdown(
        """
        <style>
        .ka-compact-cal [data-testid="column"] {
            padding-left: 1px !important;
            padding-right: 1px !important;
        }
        .ka-compact-cal [data-testid="column"] button {
            width: 100% !important;
            min-height: 2.35rem !important;
            max-height: 2.5rem !important;
            padding: 0.1rem 0 !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            line-height: 1.1 !important;
        }
        .ka-compact-cal-hdr [data-testid="column"] p {
            text-align: center !important;
            font-size: 0.68rem !important;
            margin: 0 !important;
            color: #64748b !important;
        }
        .ka-compact-cal-strip {
            height: 3px;
            border-radius: 2px;
            margin-bottom: 2px;
        }
        @media (max-width: 768px) {
            .ka-compact-cal [data-testid="column"] button {
                min-height: 2.15rem !important;
                font-size: 0.72rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _open_dialog_state(dialog_key: str, select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds
    st.session_state[dialog_key] = ds


def render_compact_month_grid(
    *,
    year: int,
    month: int,
    select_key: str,
    dialog_key: str,
    day_style: Callable[[str, int], dict],
    on_pick: Callable[[str], None] | None = None,
    firstweekday: int = 6,
) -> None:
    """
    Render minimal 7-column calendar. Each cell = color strip + day button.
    day_style(ds, day) -> {bg, border, label, disabled}
    Sets dialog_key in session_state on pick; caller opens st.dialog on rerun.
    """
    inject_compact_calendar_css()
    st.markdown('<div class="ka-compact-cal">', unsafe_allow_html=True)

    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    hdr = st.columns(7)
    for i, w in enumerate(weekdays):
        with hdr[i]:
            st.markdown(f"<p class='ka-compact-cal-hdr'>{w}</p>", unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=firstweekday)
    selected = st.session_state.get(select_key, "")

    for week in cal.monthdayscalendar(year, month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown(
                        "<div style='min-height:2.5rem;background:#f8fafc;"
                        "border-radius:4px;'></div>",
                        unsafe_allow_html=True,
                    )
                    continue
                ds = f"{year}-{month:02d}-{day:02d}"
                style = day_style(ds, day)
                bg = style.get("bg", "#f8fafc")
                border = style.get("border", "1px solid #e2e8f0")
                label = style.get("label", str(day))
                disabled = bool(style.get("disabled"))
                hint = style.get("hint", "")
                is_sel = selected == ds

                st.markdown(
                    f"<div class='ka-compact-cal-strip' style='background:{bg};"
                    f"border:{border};'></div>",
                    unsafe_allow_html=True,
                )
                if hint:
                    st.markdown(
                        f"<div style='font-size:0.58rem;text-align:center;color:#475569;"
                        f"line-height:1.05;margin:-1px 0 1px;overflow:hidden;"
                        f"white-space:nowrap;text-overflow:ellipsis;'>{hint}</div>",
                        unsafe_allow_html=True,
                    )
                btn_type = "primary" if is_sel else "secondary"
                st.button(
                    label,
                    key=f"compact_{select_key}_{ds}",
                    use_container_width=True,
                    disabled=disabled,
                    type=btn_type,
                    on_click=on_pick if on_pick else _open_dialog_state,
                    args=(ds,) if on_pick else (dialog_key, select_key, ds),
                )

    st.markdown("</div>", unsafe_allow_html=True)


def open_dialog_if_requested(
    dialog_key: str,
    render_content: Callable[[str], None],
    *,
    title: str = "訓練詳情",
) -> None:
    """Call render_content(ds) inside st.dialog when dialog_key was set by grid tap."""
    ds = st.session_state.get(dialog_key)
    if not ds:
        return

    @st.dialog(title, width="large")
    def _popup() -> None:
        render_content(ds)

    st.session_state.pop(dialog_key, None)
    _popup()
