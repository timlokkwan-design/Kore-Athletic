"""TimeTree-inspired month grid — event chips visible without tapping."""
from __future__ import annotations

import calendar
import html
from dataclasses import dataclass
from datetime import date
from typing import Callable

import streamlit as st


@dataclass(frozen=True)
class TimetreeCell:
    key_id: str
    day: int
    chips: tuple[dict, ...] = ()
    extra_count: int = 0
    tone: str = "empty"
    sync: str = ""
    disabled: bool = False
    selected: bool = False
    is_today: bool = False
    empty: bool = False
    pick_label: str = ""


def chips_html(chips: list[dict] | tuple[dict, ...], extra_count: int = 0) -> str:
    parts: list[str] = []
    for chip in chips:
        tone = html.escape(str(chip.get("tone", "empty")))
        label = html.escape(str(chip.get("label", "")))
        parts.append(f'<span class="ka-tt-chip ka-tt-chip-{tone}">{label}</span>')
    if extra_count > 0:
        parts.append(f'<span class="ka-tt-more">+{extra_count}</span>')
    return "".join(parts)


def inject_timetree_calendar_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"]:has(.ka-tt-grid-marker),
        div[data-testid="stHorizontalBlock"]:has(.ka-tt-hdr) {
            display: grid !important;
            grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
            gap: 2px !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            background: #e8ecf1 !important;
            border-radius: 10px !important;
            padding: 2px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.ka-tt-grid-marker)
        > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.ka-tt-hdr)
        > div[data-testid="column"] {
            padding: 0 !important;
            margin: 0 !important;
            min-width: 0 !important;
            flex: unset !important;
        }
        div[data-testid="column"]:has(.ka-tt-marker) {
            position: relative !important;
            min-height: 4.75rem !important;
        }
        div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stVerticalBlock"] {
            position: relative !important;
            min-height: 4.75rem !important;
            gap: 0 !important;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell {
            position: absolute;
            inset: 0;
            background: #ffffff;
            border-radius: 6px;
            padding: 3px 2px 2px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            overflow: hidden;
            box-sizing: border-box;
            pointer-events: none;
            z-index: 1;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell.ka-tt-selected {
            box-shadow: inset 0 0 0 2px #2563eb;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell.ka-tt-today .ka-tt-daynum {
            background: #2563eb;
            color: #ffffff;
            border-radius: 999px;
            width: 1.35rem;
            height: 1.35rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-daynum {
            font-size: 0.72rem;
            font-weight: 700;
            color: #334155;
            line-height: 1.2;
            padding-left: 2px;
            flex-shrink: 0;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chips {
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex: 1;
            min-height: 0;
            overflow: hidden;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip {
            display: block;
            font-size: 0.52rem;
            font-weight: 700;
            line-height: 1.15;
            padding: 2px 3px;
            border-radius: 3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            border-left: 3px solid transparent;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip-training {
            background: #dbeafe;
            color: #1e3a8a;
            border-left-color: #3b82f6;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip-competition {
            background: #fee2e2;
            color: #991b1b;
            border-left-color: #ef4444;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip-rest {
            background: #f1f5f9;
            color: #64748b;
            border-left-color: #94a3b8;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip-empty {
            background: #f8fafc;
            color: #94a3b8;
            border-left-color: #cbd5e1;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-more {
            font-size: 0.48rem;
            color: #64748b;
            font-weight: 700;
            padding-left: 2px;
        }
        div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-pick {
            position: absolute;
            top: 2px;
            right: 2px;
            font-size: 0.55rem;
            font-weight: 800;
            color: #16a34a;
            z-index: 2;
            pointer-events: none;
        }
        div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stButton"] {
            position: absolute !important;
            inset: 0 !important;
            z-index: 4 !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stButton"] button {
            opacity: 0 !important;
            width: 100% !important;
            height: 100% !important;
            min-height: 4.75rem !important;
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
        }
        div[data-testid="column"]:has(.ka-tt-marker[data-disabled="1"]) .ka-tt-cell {
            background: #f8fafc;
            opacity: 0.55;
        }
        div[data-testid="column"]:has(.ka-tt-hdr) p {
            text-align: center !important;
            font-size: 0.65rem !important;
            margin: 0 !important;
            padding: 4px 0 !important;
            color: #64748b !important;
            font-weight: 700 !important;
        }
        div[data-testid="column"]:has(.ka-tt-empty) {
            min-height: 4.75rem !important;
            background: #f8fafc;
            border-radius: 6px;
        }
        @media (max-width: 768px) {
            div[data-testid="column"]:has(.ka-tt-marker),
            div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stVerticalBlock"],
            div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stButton"] button {
                min-height: 5.25rem !important;
            }
            div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip {
                font-size: clamp(0.46rem, 2.1vw, 0.54rem);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _cell_face_html(cell: TimetreeCell) -> str:
    if cell.empty:
        return "<div class='ka-tt-empty'></div>"
    classes = ["ka-tt-cell"]
    if cell.is_today:
        classes.append("ka-tt-today")
    if cell.selected:
        classes.append("ka-tt-selected")
    sync = html.escape(cell.sync)
    pick = (
        f"<span class='ka-tt-pick'>{html.escape(cell.pick_label)}</span>"
        if cell.pick_label else ""
    )
    body = chips_html(cell.chips, cell.extra_count)
    return (
        f"<div class='{' '.join(classes)}' data-sync='{sync}'>"
        f"{pick}"
        f"<div class='ka-tt-daynum'>{cell.day}</div>"
        f"<div class='ka-tt-chips'>{body}</div>"
        f"</div>"
    )


def _render_timetree_cell(
    *,
    cell: TimetreeCell,
    button_key: str,
    on_click: Callable | None = None,
    click_args: tuple = (),
) -> None:
    if cell.empty:
        st.markdown("<div class='ka-tt-empty'></div>", unsafe_allow_html=True)
        return
    disabled_attr = "1" if cell.disabled else "0"
    st.markdown(
        f'<div class="ka-tt-marker" data-disabled="{disabled_attr}"></div>'
        f"{_cell_face_html(cell)}",
        unsafe_allow_html=True,
    )
    st.button(
        " ",
        key=button_key,
        use_container_width=True,
        disabled=cell.disabled,
        on_click=on_click,
        args=click_args,
    )


def render_timetree_row(
    cells: list[TimetreeCell],
    *,
    key_prefix: str,
    row_idx: int,
    on_click: Callable | None = None,
    click_args_fn: Callable[[TimetreeCell], tuple] | None = None,
) -> None:
    padded = list(cells[:7])
    while len(padded) < 7:
        padded.append(
            TimetreeCell(key_id=f"empty_{len(padded)}", day=0, empty=True)
        )
    st.markdown("<div class='ka-tt-grid-marker'></div>", unsafe_allow_html=True)
    cols = st.columns(7)
    for i, (col, cell) in enumerate(zip(cols, padded)):
        with col:
            args = click_args_fn(cell) if on_click and click_args_fn and not cell.empty else ()
            _render_timetree_cell(
                cell=cell,
                button_key=f"{key_prefix}_r{row_idx}_c{i}_{cell.key_id}",
                on_click=on_click if not cell.empty and not cell.disabled else None,
                click_args=args,
            )


def render_timetree_month_grid(
    *,
    year: int,
    month: int,
    select_key: str,
    dialog_key: str,
    day_style: Callable[[str, int], dict],
    on_pick: Callable[[str], None] | None = None,
    firstweekday: int = 6,
) -> None:
    inject_timetree_calendar_css()

    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    st.markdown("<div class='ka-tt-hdr'></div>", unsafe_allow_html=True)
    hdr = st.columns(7)
    for i, w in enumerate(weekdays):
        with hdr[i]:
            st.markdown(f"<p>{w}</p>", unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=firstweekday)
    selected = st.session_state.get(select_key, "")
    today_str = date.today().isoformat()

    pick_fn = on_pick if on_pick else _open_dialog_state
    if on_pick:
        def _args(cell: TimetreeCell) -> tuple:
            return (cell.key_id,)
    else:
        def _args(cell: TimetreeCell) -> tuple:
            return (dialog_key, select_key, cell.key_id)

    for row_idx, week in enumerate(cal.monthdayscalendar(year, month)):
        cells: list[TimetreeCell] = []
        for day in week:
            if day == 0:
                cells.append(
                    TimetreeCell(key_id=f"e{row_idx}_{len(cells)}", day=0, empty=True)
                )
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            style = day_style(ds, day)
            cells.append(
                TimetreeCell(
                    key_id=ds,
                    day=day,
                    chips=tuple(style.get("chips", [])),
                    extra_count=int(style.get("extra_count", 0)),
                    tone=style.get("tone", "empty"),
                    sync=style.get("sync", ""),
                    disabled=bool(style.get("disabled")),
                    selected=(selected == ds),
                    is_today=(ds == today_str),
                    pick_label=str(style.get("pick_label", "")),
                )
            )
        render_timetree_row(
            cells,
            key_prefix=f"tt_{select_key}",
            row_idx=row_idx,
            on_click=pick_fn,
            click_args_fn=_args,
        )


def _open_dialog_state(dialog_key: str, select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds
    st.session_state[dialog_key] = ds


def render_timetree_list_card(
    *,
    day: int,
    month: int,
    wd_cn: str,
    chips: list[dict],
    extra_count: int,
    is_today: bool,
    is_active: bool,
    detail: str = "",
) -> str:
    today_cls = " ka-tt-list-today" if is_today else ""
    active_cls = " ka-tt-list-active" if is_active else ""
    chip_body = chips_html(chips, extra_count)
    detail_html = (
        f"<div class='ka-tt-list-detail'>{html.escape(detail)}</div>" if detail else ""
    )
    today_tag = '<span class="ka-tt-list-today-tag">今日</span>' if is_today else ""
    rest = '<span class="ka-tt-list-rest">休息</span>' if not chip_body else chip_body
    return (
        f"<div class='ka-tt-list-card{today_cls}{active_cls}'>"
        f"<div class='ka-tt-list-head'>"
        f"<span class='ka-tt-list-date'>{month}/{day:02d}</span>"
        f"<span class='ka-tt-list-wd'>{wd_cn}</span>"
        f"{today_tag}"
        f"</div>"
        f"<div class='ka-tt-list-chips'>{rest}</div>"
        f"{detail_html}"
        f"</div>"
    )


def inject_timetree_list_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) {
            position: relative;
            margin-bottom: 0.35rem;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 10px 12px;
            pointer-events: none;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-card.ka-tt-list-active {
            border-color: #2563eb;
            box-shadow: 0 0 0 1px #2563eb;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-head {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-date {
            font-size: 1rem;
            font-weight: 800;
            color: #1e3a8a;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-wd {
            font-size: 0.82rem;
            color: #64748b;
            font-weight: 600;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-today-tag {
            font-size: 0.68rem;
            background: #dbeafe;
            color: #1d4ed8;
            padding: 2px 8px;
            border-radius: 999px;
            font-weight: 700;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-chips {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-chip {
            display: block;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 5px 8px;
            border-radius: 6px;
            border-left: 4px solid transparent;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-chip-training {
            background: #dbeafe;
            color: #1e3a8a;
            border-left-color: #3b82f6;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-chip-competition {
            background: #fee2e2;
            color: #991b1b;
            border-left-color: #ef4444;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-chip-rest {
            background: #f1f5f9;
            color: #64748b;
            border-left-color: #94a3b8;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-rest {
            font-size: 0.82rem;
            color: #94a3b8;
            font-weight: 600;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-detail {
            font-size: 0.75rem;
            color: #64748b;
            margin-top: 6px;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) [data-testid="stButton"] {
            position: absolute !important;
            inset: 0 !important;
            z-index: 2 !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) [data-testid="stButton"] button {
            opacity: 0 !important;
            width: 100% !important;
            height: 100% !important;
            min-height: 3.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
