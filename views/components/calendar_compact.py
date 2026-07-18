"""Compact 7-column month grid — uniform square cells, dialog on tap."""
from __future__ import annotations

import calendar
import html
from dataclasses import dataclass
from datetime import date
from typing import Callable

import streamlit as st

_TONE_STYLES = {
    "training": ("#dbeafe", "#1e40af", "#93c5fd"),
    "competition": ("#fee2e2", "#991b1b", "#fca5a5"),
    "rest": ("#f1f5f9", "#64748b", "#e2e8f0"),
    "empty": ("#f8fafc", "#64748b", "#e2e8f0"),
    "picked": ("#dcfce7", "#166534", "#86efac"),
    "attended": ("#dcfce7", "#166534", "#86efac"),
    "disabled": ("#f8fafc", "#cbd5e1", "#f1f5f9"),
}


@dataclass(frozen=True)
class SquareCell:
    key_id: str
    label: str
    tone: str = "empty"
    sync: str = ""
    disabled: bool = False
    selected: bool = False
    empty: bool = False


def inject_compact_calendar_css() -> None:
    tone_rules = []
    for tone, (bg, fg, border) in _TONE_STYLES.items():
        tone_rules.append(
            f'div[data-testid="column"]:has(.ka-ccell-marker[data-tone="{tone}"]) '
            f'[data-testid="stButton"] button {{'
            f"background-color: {bg} !important;"
            f"color: {fg} !important;"
            f"border: 1px solid {border} !important;"
            f"}}"
        )
    tone_css = "\n".join(tone_rules)

    st.markdown(
        f"""
        <style>
        div[data-testid="stHorizontalBlock"]:has(.ka-ccell-marker),
        div[data-testid="stHorizontalBlock"]:has(.ka-ccell-hdr) {{
            display: grid !important;
            grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
            gap: 2px !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            max-width: 100% !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(.ka-ccell-marker)
        > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.ka-ccell-hdr)
        > div[data-testid="column"] {{
            padding: 0 !important;
            margin: 0 !important;
            min-width: 0 !important;
            width: auto !important;
            max-width: none !important;
            flex: unset !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) {{
            aspect-ratio: 1 / 1 !important;
            overflow: hidden !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stVerticalBlock"] {{
            gap: 0 !important;
            height: 100% !important;
            min-height: 0 !important;
            justify-content: stretch !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) .ka-ccell-marker {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stButton"] {{
            position: absolute !important;
            inset: 0 !important;
            width: 100% !important;
            height: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) {{
            position: relative !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stButton"] button {{
            position: absolute !important;
            inset: 0 !important;
            width: 100% !important;
            height: 100% !important;
            min-height: 0 !important;
            max-height: none !important;
            padding: 0 !important;
            margin: 0 !important;
            font-size: 0.68rem !important;
            font-weight: 600 !important;
            line-height: 1 !important;
            overflow: hidden !important;
            -webkit-appearance: none !important;
            appearance: none !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06) !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker[data-selected="1"]) [data-testid="stButton"] button {{
            box-shadow: inset 0 0 0 2px #1d4ed8 !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker[data-sync="workout"]) [data-testid="stButton"] button {{
            box-shadow: inset 0 0 0 2px #f59e0b !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker[data-sync="schedule"]) [data-testid="stButton"] button {{
            box-shadow: inset 0 0 0 2px #ea580c !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker[data-sync="both"]) [data-testid="stButton"] button {{
            box-shadow: inset 0 0 0 2px #f59e0b, inset 0 0 0 3px #ea580c !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-marker[data-sync="copy-source"]) [data-testid="stButton"] button {{
            box-shadow: inset 0 0 0 3px #f59e0b !important;
        }}
        {tone_css}
        div[data-testid="column"]:has(.ka-ccell-empty) {{
            aspect-ratio: 1 / 1 !important;
        }}
        div[data-testid="column"]:has(.ka-ccell-empty) .ka-ccell-empty {{
            width: 100% !important;
            height: 100% !important;
            min-height: 100% !important;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #f1f5f9;
            box-sizing: border-box;
        }}
        div[data-testid="column"]:has(.ka-ccell-hdr) p {{
            text-align: center !important;
            font-size: 0.62rem !important;
            margin: 0 !important;
            padding: 2px 0 !important;
            color: #64748b !important;
            font-weight: 600 !important;
        }}
        @media (max-width: 768px) {{
            section.main .block-container {{
                padding-left: 0.35rem !important;
                padding-right: 0.35rem !important;
            }}
            div[data-testid="stHorizontalBlock"]:has(.ka-ccell-marker),
            div[data-testid="stHorizontalBlock"]:has(.ka-ccell-hdr) {{
                gap: 1px !important;
            }}
            div[data-testid="column"]:has(.ka-ccell-marker) [data-testid="stButton"] button {{
                font-size: clamp(0.48rem, 2.4vw, 0.62rem) !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _open_dialog_state(dialog_key: str, select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds
    st.session_state[dialog_key] = ds


def _render_square_cell(
    *,
    cell: SquareCell,
    button_key: str,
    on_click: Callable | None = None,
    click_args: tuple = (),
) -> None:
    if cell.empty:
        st.markdown("<div class='ka-ccell-marker ka-ccell-empty'></div>", unsafe_allow_html=True)
        return
    st.markdown(
        f'<div class="ka-ccell-marker" data-tone="{html.escape(cell.tone)}" '
        f'data-selected="{"1" if cell.selected else "0"}" '
        f'data-sync="{html.escape(cell.sync)}"></div>',
        unsafe_allow_html=True,
    )
    st.button(
        cell.label,
        key=button_key,
        use_container_width=True,
        disabled=cell.disabled,
        type="secondary",
        on_click=on_click,
        args=click_args,
    )


def render_seven_column_row(
    cells: list[SquareCell],
    *,
    key_prefix: str,
    row_idx: int,
    on_click: Callable | None = None,
    click_args_fn: Callable[[SquareCell], tuple] | None = None,
) -> None:
    padded = list(cells[:7])
    while len(padded) < 7:
        padded.append(SquareCell(key_id=f"empty_{len(padded)}", label="", empty=True))
    cols = st.columns(7)
    for i, (col, cell) in enumerate(zip(cols, padded)):
        with col:
            args = click_args_fn(cell) if on_click and click_args_fn and not cell.empty else ()
            _render_square_cell(
                cell=cell,
                button_key=f"{key_prefix}_r{row_idx}_c{i}_{cell.key_id}",
                on_click=on_click if not cell.empty and not cell.disabled else None,
                click_args=args,
            )


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
    inject_compact_calendar_css()

    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    hdr = st.columns(7)
    for i, w in enumerate(weekdays):
        with hdr[i]:
            st.markdown(f"<div class='ka-ccell-hdr'><p>{w}</p></div>", unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=firstweekday)
    selected = st.session_state.get(select_key, "")

    pick_fn = on_pick if on_pick else _open_dialog_state
    if on_pick:
        def _args(cell: SquareCell) -> tuple:
            return (cell.key_id,)
    else:
        def _args(cell: SquareCell) -> tuple:
            return (dialog_key, select_key, cell.key_id)

    for row_idx, week in enumerate(cal.monthdayscalendar(year, month)):
        cells: list[SquareCell] = []
        for day in week:
            if day == 0:
                cells.append(SquareCell(key_id=f"e{row_idx}_{len(cells)}", label="", empty=True))
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            style = day_style(ds, day)
            raw_label = style.get("label", str(day))
            label = str(day)
            if raw_label.startswith("●"):
                label = f"●{day}"
            cells.append(
                SquareCell(
                    key_id=ds,
                    label=label,
                    tone=style.get("tone", "empty"),
                    sync=style.get("sync", ""),
                    disabled=bool(style.get("disabled")),
                    selected=(selected == ds),
                )
            )
        render_seven_column_row(
            cells,
            key_prefix=f"cal_{select_key}",
            row_idx=row_idx,
            on_click=pick_fn,
            click_args_fn=_args,
        )


def open_dialog_if_requested(
    dialog_key: str,
    render_content: Callable[[str], None],
    *,
    title: str = "訓練詳情",
) -> None:
    ds = st.session_state.get(dialog_key)
    if not ds:
        return

    @st.dialog(title, width="large")
    def _popup() -> None:
        render_content(ds)

    st.session_state.pop(dialog_key, None)
    _popup()
