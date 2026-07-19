"""TimeTree-inspired month grid — event chips visible without tapping."""
from __future__ import annotations

import calendar
import html
from dataclasses import dataclass
from datetime import date
from typing import Callable

import streamlit as st

from views.components.calendar_theme import inject_calendar_theme


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
    # Markers MUST live inside columns so :has(.ka-tt-…) matches this row.
    # (External markers never matched stHorizontalBlock — calendar stacked on mobile.)
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
    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    # Put ka-tt-hdr inside each column so the 7-col grid CSS can match.
    hdr = st.columns(7)
    for i, w in enumerate(weekdays):
        with hdr[i]:
            st.markdown(
                f"<div class='ka-tt-hdr'><p>{w}</p></div>",
                unsafe_allow_html=True,
            )

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
    """List cards share the unified calendar theme."""
    inject_calendar_theme()
