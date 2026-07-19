"""Mobile-friendly month list view (alternative to 7-column grid)."""
from __future__ import annotations

import calendar
from datetime import date
from typing import Callable

import streamlit as st

from utils.helpers import calendar_day_event_chips
from views.components.calendar_theme import (
    ACCENT_SELECTED_RING,
    CALENDAR_TONES,
    inject_calendar_theme,
)
from views.components.calendar_timetree import render_timetree_list_card


def _select_list_date(select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds


def _select_list_date_coach_edit(select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds
    st.session_state["coach_prog_screen"] = "edit"


def _toggle_list_pick(pick_key: str, ds: str) -> None:
    picks_list = list(st.session_state.get(pick_key, []))
    if ds in picks_list:
        picks_list.remove(ds)
    else:
        picks_list.append(ds)
    st.session_state[pick_key] = sorted(picks_list)


def _set_view_mode(mode_key: str, mode: str) -> None:
    st.session_state[mode_key] = mode


def _normalize_view_mode(mode_key: str, default_mode: str = "grid") -> str:
    """Migrate legacy radio labels; default_mode is 'grid' or 'list'."""
    raw = st.session_state.get(mode_key)
    if raw == "grid" or raw == "list":
        return raw
    if isinstance(raw, str) and raw.startswith("📋"):
        st.session_state[mode_key] = "list"
        return "list"
    st.session_state[mode_key] = default_mode
    return default_mode


def _inject_view_toggle_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(.ka-cal-view-marker) [data-testid="stHorizontalBlock"] button {
            min-height: 2.6rem !important;
            font-size: 0.92rem !important;
            font-weight: 700 !important;
        }
        @media (max-width: 768px) {
            div[data-testid="stVerticalBlock"]:has(.ka-cal-view-marker) [data-testid="stHorizontalBlock"] button {
                min-height: 2.85rem !important;
                font-size: 0.95rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_view_mode_toggle(
    key: str,
    *,
    force_grid: bool = False,
    default_mode: str = "grid",
) -> str:
    """Return 'grid' or 'list'. Mobile-friendly pill buttons."""
    mode_key = f"{key}_view_mode"
    if force_grid:
        st.session_state[mode_key] = "grid"
        return "grid"

    current = _normalize_view_mode(mode_key, default_mode)
    _inject_view_toggle_css()

    st.caption("檢視方式")
    st.markdown('<div class="ka-cal-view-marker"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.button(
            "📅 月曆",
            key=f"{key}_vm_grid",
            use_container_width=True,
            type="primary" if current == "grid" else "secondary",
            on_click=_set_view_mode,
            args=(mode_key, "grid"),
        )
    with c2:
        st.button(
            "📋 列表",
            key=f"{key}_vm_list",
            use_container_width=True,
            type="primary" if current == "list" else "secondary",
            on_click=_set_view_mode,
            args=(mode_key, "list"),
        )
    return _normalize_view_mode(mode_key, default_mode)


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
    goto_edit_on_select: bool = False,
) -> None:
    prog = prog_map.get(ds)
    title, detail, type_label, bg = describe_day(ds, prog)
    d = date.fromisoformat(ds)
    is_today = ds == today.isoformat()

    active = (not pick_mode) and st.session_state.get(select_key) == ds
    t_train = CALENDAR_TONES["training"]
    border = f"2px solid {ACCENT_SELECTED_RING}" if active else "1px solid #C5CED8"
    cell_bg = bg
    if pick_mode == "copy" and ds == copy_source:
        border = f"3px solid {CALENDAR_TONES['competition']['accent']}"
    elif pick_mode == "delete" and ds in picks:
        border = f"3px solid {CALENDAR_TONES['competition']['accent']}"
        cell_bg = CALENDAR_TONES["competition"]["bg"]
    elif pick_mode and ds in picks:
        border = f"3px solid {CALENDAR_TONES['picked']['accent']}"
        cell_bg = CALENDAR_TONES["picked"]["bg"]
    elif is_today:
        border = f"2px solid {ACCENT_SELECTED_RING}"

    main_title = title or empty_label

    if pick_mode:
        label_col, btn_col = st.columns([5, 1])
        with label_col:
            type_badge = (
                f"<span style='background:{t_train['bg']};color:{t_train['fg']};padding:2px 8px;"
                f"border-radius:999px;font-size:12px;margin-left:8px;"
                f"border:1px solid {t_train['border']};'>{type_label}</span>"
                if type_label else ""
            )
            detail_html = (
                f"<div style='font-size:13px;color:#374151;margin-top:4px;'>{detail}</div>"
                if detail else ""
            )
            st.markdown(
                f"<div style='background:{cell_bg};border:{border};border-radius:12px;"
                f"padding:12px 14px;margin-bottom:6px;'>"
                f"<div style='font-size:15px;font-weight:800;color:#111827;'>"
                f"{month}/{day:02d}（{wd_cn}）{type_badge}</div>"
                f"<div style='font-size:14px;font-weight:600;margin-top:4px;'>"
                f"{main_title}</div>"
                f"{detail_html}</div>",
                unsafe_allow_html=True,
            )
        with btn_col:
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
        return

    chips, extra = calendar_day_event_chips(prog, max_chips=3)
    card = render_timetree_list_card(
        day=day,
        month=month,
        wd_cn=wd_cn,
        chips=chips,
        extra_count=extra,
        is_today=is_today,
        is_active=active,
        detail=detail,
    )
    st.markdown(f'<div class="ka-tt-list-wrap"></div>{card}', unsafe_allow_html=True)
    st.button(
        " ",
        key=f"list_sel_{select_key}_{ds}",
        use_container_width=True,
        on_click=_select_list_date_coach_edit if goto_edit_on_select else _select_list_date,
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
    goto_edit_on_select: bool = False,
) -> date:
    """
    Vertical list of days in month.
    describe_day(ds, prog) -> (title, detail, type_label, bg_color)
    """
    inject_calendar_theme()
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
            goto_edit_on_select=goto_edit_on_select,
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
