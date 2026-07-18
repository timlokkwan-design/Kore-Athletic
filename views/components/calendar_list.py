"""Mobile-friendly month list view (alternative to 7-column grid)."""
from __future__ import annotations

import calendar
from datetime import date
from typing import Callable

import streamlit as st


def render_view_mode_toggle(key: str) -> str:
    """Return 'grid' or 'list'."""
    choice = st.radio(
        "檢視方式",
        ["📅 月曆", "📋 列表（手機推薦）"],
        horizontal=True,
        key=f"{key}_view_mode",
        label_visibility="collapsed",
    )
    return "list" if choice.startswith("📋") else "grid"


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
) -> date:
    """
    Vertical list of days in month.
    describe_day(ds, prog) -> (title, detail, type_label, bg_color)
    """
    picks = set(st.session_state.get(pick_key, []))
    if select_key not in st.session_state:
        st.session_state[select_key] = date.today().isoformat()

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    wd_names = ["一", "二", "三", "四", "五", "六", "日"]

    for week in weeks:
        for day in week:
            if day == 0:
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            d = date.fromisoformat(ds)
            prog = prog_map.get(ds)
            title, detail, type_label, bg = describe_day(ds, prog)
            wd_cn = wd_names[d.weekday()]

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
                    f"{month}/{day:02d}（{wd_cn}）{type_badge}</div>"
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
                        if st.button(
                            "✓" if picked else ("🗑" if pick_mode == "delete" else "＋"),
                            key=f"list_{select_key}_{ds}",
                            use_container_width=True,
                        ):
                            if pick_mode == "copy" and ds == copy_source:
                                st.session_state["sched_flash"] = ("error", "來源日期不能選為目標")
                            elif pick_mode == "delete" and can_pick is not None and not can_pick(ds, prog):
                                st.session_state["sched_flash"] = ("error", f"{ds} 沒有已儲存的課表")
                            else:
                                picks_list = list(st.session_state.get(pick_key, []))
                                if ds in picks_list:
                                    picks_list.remove(ds)
                                else:
                                    picks_list.append(ds)
                                st.session_state[pick_key] = sorted(picks_list)
                            st.rerun()
                elif st.button("選", key=f"list_{select_key}_{ds}", use_container_width=True):
                    st.session_state[select_key] = ds
                    st.rerun()

    return date.fromisoformat(str(st.session_state[select_key]))
