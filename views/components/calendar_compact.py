"""Compact 7-column month grid — uniform square cells, dialog on tap."""
from __future__ import annotations

import calendar
from datetime import date
from typing import Callable

import streamlit as st

# Target cell size (px); width follows 1/7 column — aspect-ratio keeps squares on mobile
_CELL_MIN = 40
_CELL_MAX = 56


def inject_compact_calendar_css() -> None:
    st.markdown(
        f"""
        <style>
        /* Scope via marker div (.ka-ccell) inside each Streamlit column block */
        div[data-testid="stHorizontalBlock"]:has(.ka-ccell-marker) {{
            gap: 2px !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(.ka-ccell-marker)
        > div[data-testid="column"] {{
            padding-left: 1px !important;
            padding-right: 1px !important;
            min-width: 0 !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stVerticalBlock"] {{
            gap: 0 !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) .ka-ccell-strip {{
            height: 4px;
            min-height: 4px;
            border-radius: 2px 2px 0 0;
            margin: 0;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stButton"] {{
            margin-top: 0 !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stButton"] button {{
            width: 100% !important;
            aspect-ratio: 1 / 1 !important;
            min-height: {_CELL_MIN}px !important;
            max-height: {_CELL_MAX}px !important;
            height: auto !important;
            padding: 2px 1px !important;
            margin: 0 !important;
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            line-height: 1.05 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 0 0 4px 4px !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-empty) .ka-ccell-empty {{
            aspect-ratio: 1 / 1;
            width: 100%;
            min-height: {_CELL_MIN}px;
            max-height: {_CELL_MAX}px;
            background: #f8fafc;
            border-radius: 4px;
            border: 1px solid #f1f5f9;
            box-sizing: border-box;
        }}
        div[data-testid="column"]:has(.ka-ccell-hdr) p {{
            text-align: center !important;
            font-size: 0.68rem !important;
            margin: 0 !important;
            color: #64748b !important;
            font-weight: 600 !important;
        }}
        @media (max-width: 768px) {{
            div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stButton"] button {{
                min-height: 36px !important;
                max-height: 48px !important;
                font-size: 0.64rem !important;
            }}
            div[data-testid="column"]:has(.ka-ccell-empty) .ka-ccell-empty {{
                min-height: 36px !important;
                max-height: 48px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _open_dialog_state(dialog_key: str, select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds
    st.session_state[dialog_key] = ds


def _compact_label(raw: str, day: int, *, max_len: int = 8) -> str:
    """Keep cell label short so every square stays one line."""
    text = raw if raw else str(day)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


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
    Render minimal 7-column calendar. Each cell = color strip + day button (fixed square).
    day_style(ds, day) -> {bg, border, label, disabled, hint (ignored in grid)}
    """
    inject_compact_calendar_css()

    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    hdr = st.columns(7)
    for i, w in enumerate(weekdays):
        with hdr[i]:
            st.markdown(
                f"<div class='ka-ccell-hdr'><p>{w}</p></div>",
                unsafe_allow_html=True,
            )

    cal = calendar.Calendar(firstweekday=firstweekday)
    selected = st.session_state.get(select_key, "")

    for week in cal.monthdayscalendar(year, month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown(
                        "<div class='ka-ccell-marker ka-ccell-empty'></div>",
                        unsafe_allow_html=True,
                    )
                    continue
                ds = f"{year}-{month:02d}-{day:02d}"
                style = day_style(ds, day)
                bg = style.get("bg", "#f8fafc")
                border = style.get("border", "1px solid #e2e8f0")
                label = _compact_label(style.get("label", str(day)), day)
                disabled = bool(style.get("disabled"))
                is_sel = selected == ds

                st.markdown(
                    "<div class='ka-ccell-marker'>"
                    f"<div class='ka-ccell-strip' style='background:{bg};"
                    f"border:{border};border-bottom:none;'></div>"
                    "</div>",
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
