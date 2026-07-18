"""Mobile-friendly month list view (alternative to 7-column grid)."""
from __future__ import annotations

import calendar
from datetime import date
from typing import Callable

import streamlit as st


def _select_list_date(select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds


def _toggle_list_pick(pick_key: str, ds: str) -> None:
    picks_list = list(st.session_state.get(pick_key, []))
    if ds in picks_list:
        picks_list.remove(ds)
    else:
        picks_list.append(ds)
    st.session_state[pick_key] = sorted(picks_list)


def render_view_mode_toggle(key: str) -> str:
    """Return 'grid' or 'list'."""
    choice = st.radio(
        "檢視方式",
        ["📅 月曆", "📋 列表"],
        horizontal=True,
        key=f"{key}_view_mode",
        label_visibility="collapsed",
    )
    return "list" if choice.startswith("📋") else "grid"


def _render_list_day_row(
    *,
    ds: str,
    day: int,
    month: int,
    wd_cn: str,
    select_key: str,
    prog_map: dict[str, dict],
    describe_day: Callable[[str, dict | None], tuple[str, str, str, str]],
    pick_mode: str | None,
    pick_key: str,
    copy_source: str,
    picks: set,
    can_pick: Callable[[str, dict | None], bool] | None,
    empty_label: str,
    today: date,
) -> None:
    prog = prog_map.get(ds)
    title, detail, type_label, bg = describe_day(ds, prog)
    d = date.fromisoformat(ds)
    is_today = ds == today.isoformat()

    active = (not pick_mode) and st.session_state.get(select_key) == ds
    border = "2px solid #1d4ed8" if active else "1px solid #e2e8f0"
    cell_bg = bg
    if pick_mode == "copy" and ds == copy_source:
        border = "3px solid #f59e0b"
    elif pick_mode == "delete" and ds in picks:
        border = "3px solid #dc2626"
        cell_bg = "#fee2e2"
    elif pick_mode and ds in picks:
        border = "3px solid #16a34a"
        cell_bg = "#dcfce7"
    elif is_today:
        border = "2px solid #1d4ed8"

    today_badge = (
        "<span style='background:#dbeafe;color:#1d4ed8;padding:2px 8px;"
        "border-radius:999px;font-size:11px;margin-left:6px;'>今日</span>"
        if is_today else ""
    )
    type_badge = (
        f"<span style='background:#e2e8f0;color:#334155;padding:2px 8px;"
        f"border-radius:999px;font-size:12px;margin-left:8px;'>{type_label}</span>"
        if type_label else ""
    )
    detail_html = (
        f"<div style='font-size:13px;color:#64748b;margin-top:4px;'>{detail}</div>"
        if detail else ""
    )

    label_col, btn_col = st.columns([5, 1])
    with label_col:
        st.markdown(
            f"<div style='background:{cell_bg};border:{border};border-radius:10px;"
            f"padding:12px 14px;margin-bottom:6px;'>"
            f"<div style='font-size:15px;font-weight:700;color:#1e3a8a;'>"
            f"{month}/{day:02d}（{wd_cn}）{today_badge}{type_badge}</div>"
            f"<div style='font-size:14px;font-weight:600;margin-top:4px;'>"
            f"{title or empty_label}</div>"
            f"{detail_html}</div>",
            unsafe_allow_html=True,
        )
    with btn_col:
        if pick_mode:
            if pick_mode == "copy" and ds == copy_source:
                st.caption("來源")
            elif can_pick is not None and not can_pick(ds, prog):
                st.caption("—")
            else:
                picked = ds in picks
                st.button(
                    "✓" if picked else ("🗑" if pick_mode == "delete" else "＋"),
                    key=f"list_{select_key}_{ds}",
                    use_container_width=True,
                    on_click=_toggle_list_pick,
                    args=(pick_key, ds),
                )
        st.button(
            "選",
            key=f"list_sel_{select_key}_{ds}",
            use_container_width=True,
            on_click=_select_list_date,
            args=(select_key, ds),
        )


def render_month_day_list(
    *,
    year: int,
    month: int,
    select_key: str,
    prog_map: dict[str, dict],
    describe_day: Callable[[str, dict | None], tuple[str, str, str, str]],
    pick_mode: str | None = None,
    pick_key: str = "pick_dates",
    copy_source: str = "",
    empty_label: str = "休息",
    can_pick: Callable[[str, dict | None], bool] | None = None,
    hide_past_days: bool = False,
    day_priority: Callable[[str, dict | None], int] | None = None,
) -> date:
    """
    Vertical list of days in month.
    describe_day(ds, prog) -> (title, detail, type_label, bg_color)
    """
    picks = set(st.session_state.get(pick_key, []))
    if select_key not in st.session_state:
        st.session_state[select_key] = date.today().isoformat()

    today = date.today()
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    wd_names = ["一", "二", "三", "四", "五", "六", "日"]

    entries: list[tuple[str, int, date]] = []
    for week in weeks:
        for day in week:
            if day == 0:
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            entries.append((ds, day, date.fromisoformat(ds)))

    def _row(ds: str, day: int, d: date) -> None:
        _render_list_day_row(
            ds=ds,
            day=day,
            month=month,
            wd_cn=wd_names[d.weekday()],
            select_key=select_key,
            prog_map=prog_map,
            describe_day=describe_day,
            pick_mode=pick_mode,
            pick_key=pick_key,
            copy_source=copy_source,
            picks=picks,
            can_pick=can_pick,
            empty_label=empty_label,
            today=today,
        )

    use_hide = hide_past_days and not pick_mode and year == today.year and month == today.month
    if use_hide:
        past = [e for e in entries if e[2] < today]
        upcoming = [e for e in entries if e[2] >= today]
        if day_priority:
            upcoming.sort(
                key=lambda e: (
                    day_priority(e[0], prog_map.get(e[0])),
                    0 if e[2] == today else 1,
                    e[2],
                )
            )
        else:
            upcoming.sort(key=lambda e: (0 if e[2] == today else 1, e[2]))
        for ds, day, d in upcoming:
            _row(ds, day, d)
        if past:
            with st.expander(f"📁 過往日期（{len(past)} 天）", expanded=False):
                for ds, day, d in past:
                    _row(ds, day, d)
    else:
        if day_priority:
            entries.sort(key=lambda e: (day_priority(e[0], prog_map.get(e[0])), e[2]))
        for ds, day, d in entries:
            _row(ds, day, d)

    return date.fromisoformat(str(st.session_state[select_key]))
