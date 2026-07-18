"""V6-style month calendar grid."""

import calendar
from datetime import date

import streamlit as st

from utils.acwr import acwr_status, calc_acwr
from utils.config import TRAIN_TYPES, TYPE_CATEGORY_COLORS
from utils.data_store import (
    build_coach_prog_map,
    ensure_program_dict,
    get_all_logs,
    get_programs_for_month,
    get_student_names,
    row_to_program,
)
from utils.helpers import normalize_date_str, program_calendar_summary, safe_str, short_group_label
from views.components.calendar_list import render_month_day_list, render_view_mode_toggle


def _sync_selection_to_month(select_key: str, year: int, month: int) -> None:
    """Keep selected date within the visible calendar month."""
    cur = st.session_state.get(select_key, date.today().isoformat())
    try:
        sel = date.fromisoformat(str(cur))
    except ValueError:
        sel = date.today()
    if sel.year == year and sel.month == month:
        return
    today = date.today()
    if today.year == year and today.month == month:
        st.session_state[select_key] = today.isoformat()
    else:
        st.session_state[select_key] = f"{year}-{month:02d}-01"


def _toggle_copy_target(ds: str, copy_source: str) -> None:
    if ds == copy_source:
        st.session_state["copy_flash"] = ("error", "來源日期不能選為目標")
        return
    targets = list(st.session_state.get("copy_target_dates", []))
    if ds in targets:
        targets.remove(ds)
    else:
        targets.append(ds)
    st.session_state.copy_target_dates = sorted(targets)


def _toggle_delete_target(ds: str) -> None:
    targets = list(st.session_state.get("delete_target_dates", []))
    if ds in targets:
        targets.remove(ds)
    else:
        targets.append(ds)
    st.session_state.delete_target_dates = sorted(targets)


def _select_calendar_date(select_key: str, ds: str) -> None:
    st.session_state[select_key] = ds


def _calendar_prev_month(select_key: str, copy_mode: bool, delete_mode: bool) -> None:
    if st.session_state.cal_month == 1:
        st.session_state.cal_month, st.session_state.cal_year = 12, st.session_state.cal_year - 1
    else:
        st.session_state.cal_month -= 1
    if not copy_mode and not delete_mode:
        _sync_selection_to_month(select_key, st.session_state.cal_year, st.session_state.cal_month)


def _calendar_next_month(select_key: str, copy_mode: bool, delete_mode: bool) -> None:
    if st.session_state.cal_month == 12:
        st.session_state.cal_month, st.session_state.cal_year = 1, st.session_state.cal_year + 1
    else:
        st.session_state.cal_month += 1
    if not copy_mode and not delete_mode:
        _sync_selection_to_month(select_key, st.session_state.cal_year, st.session_state.cal_month)


def _render_calendar_grid(
    select_key: str,
    year: int,
    month: int,
    prog_map: dict[str, dict],
    show_acwr: bool,
    copy_mode: bool,
    delete_mode: bool,
    copy_source: str,
    copy_targets: set,
    delete_targets: set,
) -> date:
    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    hdr = st.columns(7)
    for i, w in enumerate(weekdays):
        hdr[i].markdown(f"**{w}**")

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    acwr_athlete = None
    logs = None
    if show_acwr and not copy_mode and not delete_mode:
        logs = get_all_logs()
        athlete_names = get_student_names()
        acwr_athlete = athlete_names[0] if athlete_names else None

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown(
                    "<div style='min-height:72px;background:#f8fafc;border-radius:4px;'></div>",
                    unsafe_allow_html=True,
                )
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            prog = ensure_program_dict(prog_map.get(ds))
            tp = safe_str(prog.get("type"))
            cat = TRAIN_TYPES.get(tp, {}).get("category", "rest")
            bg = TYPE_CATEGORY_COLORS.get(cat, "#f1f5f9")
            active = (not copy_mode and not delete_mode) and st.session_state[select_key] == ds
            if copy_mode and ds == copy_source:
                border = "3px solid #f59e0b"
                weight = "bold"
            elif copy_mode and ds in copy_targets:
                border = "3px solid #16a34a"
                bg = "#dcfce7"
                weight = "bold"
            elif copy_mode:
                border = "2px dashed #86efac"
                weight = "normal"
            elif delete_mode and ds in delete_targets:
                border = "3px solid #dc2626"
                bg = "#fee2e2"
                weight = "bold"
            elif delete_mode and ds in prog_map:
                border = "2px dashed #fca5a5"
                weight = "normal"
            elif delete_mode:
                border = "1px solid #f1f5f9"
                weight = "normal"
                bg = "#f8fafc"
            elif active:
                border = "3px solid #1d4ed8"
                weight = "bold"
            else:
                border = "1px solid #e2e8f0"
                weight = "normal"
            title_line, spec_line = program_calendar_summary(prog) if prog else ("", "")
            acwr_html = ""
            if show_acwr and acwr_athlete and not copy_mode and not delete_mode:
                v, _ = acwr_status(calc_acwr(logs, acwr_athlete, date.fromisoformat(ds)))
                acwr_html = f"<br><small style='color:#64748b;'>ACWR {v}</small>"
            btn_label = f"{day}"
            if tp and not copy_mode and not delete_mode:
                btn_label = f"{day} · {tp[:2]}"
            if copy_mode and ds != copy_source:
                cols[i].button(
                    f"✓ {day}" if ds in copy_targets else f"+ {day}",
                    key=f"{select_key}_{ds}",
                    use_container_width=True,
                    on_click=_toggle_copy_target,
                    args=(ds, copy_source),
                )
            elif delete_mode and ds in prog_map:
                cols[i].button(
                    f"✓ {day}" if ds in delete_targets else f"🗑 {day}",
                    key=f"{select_key}_{ds}",
                    use_container_width=True,
                    on_click=_toggle_delete_target,
                    args=(ds,),
                )
            elif delete_mode:
                cols[i].button(
                    f"— {day}",
                    key=f"{select_key}_{ds}",
                    use_container_width=True,
                    disabled=True,
                )
            else:
                cols[i].button(
                    btn_label,
                    key=f"{select_key}_{ds}",
                    use_container_width=True,
                    on_click=_select_calendar_date,
                    args=(select_key, ds),
                )
            spec_html = f"<br><span style='color:#475569;'>{spec_line}</span>" if spec_line else ""
            cols[i].markdown(
                f"<div style='background:{bg};border:{border};border-radius:4px;padding:3px 4px;"
                f"min-height:44px;font-size:10px;line-height:1.25;margin-top:-6px;font-weight:{weight};'>"
                f"<span style='color:#1e3a8a;font-weight:600;'>{title_line or '—'}</span>"
                f"{spec_html}{acwr_html}</div>",
                unsafe_allow_html=True,
            )

    return date.fromisoformat(st.session_state[select_key])


def render_calendar(
    select_key: str = "cal_select",
    show_acwr: bool = False,
    copy_mode: bool = False,
    delete_mode: bool = False,
) -> date | None:
    return _render_calendar_impl(select_key, show_acwr, copy_mode, delete_mode)


def _render_calendar_impl(
    select_key: str,
    show_acwr: bool,
    copy_mode: bool,
    delete_mode: bool,
) -> date | None:
    if "cal_year" not in st.session_state:
        t = date.today()
        st.session_state.cal_year, st.session_state.cal_month = t.year, t.month

    copy_source = st.session_state.get("copy_source_date", "") if copy_mode else ""
    copy_targets = set(st.session_state.get("copy_target_dates", [])) if copy_mode else set()
    delete_targets = set(st.session_state.get("delete_target_dates", [])) if delete_mode else set()

    c1, c2, c3 = st.columns([1, 2, 1])
    c1.button(
        "◀ 上月",
        key=f"{select_key}_prev",
        on_click=_calendar_prev_month,
        args=(select_key, copy_mode, delete_mode),
    )
    c2.markdown(f"### {st.session_state.cal_year} 年 {st.session_state.cal_month:02d} 月")
    c3.button(
        "下月 ▶",
        key=f"{select_key}_next",
        on_click=_calendar_next_month,
        args=(select_key, copy_mode, delete_mode),
    )

    if copy_mode:
        st.caption("🟧 橙色=來源 · 🟩 綠色=已選目標（可跨月多選）· 點一下選取/取消")
    elif delete_mode:
        st.caption("🟥 紅色=已選刪除 · 虛線=有課表可選 · 灰底=無課表 · 可跨月多選")
    else:
        st.caption("🟥速度 🟦耐力 🟪技術 🟧肌力 🟩比賽 ⬜休息 · 手機請用「列表」檢視")

    year, month = st.session_state.cal_year, st.session_state.cal_month
    if not copy_mode and not delete_mode:
        _sync_selection_to_month(select_key, year, month)
    programs = get_programs_for_month(year, month)
    prog_map = build_coach_prog_map(programs)

    if select_key not in st.session_state:
        st.session_state[select_key] = date.today().isoformat()

    view_mode = render_view_mode_toggle(select_key)
    if view_mode == "list":
        athlete_names = get_student_names()
        acwr_athlete = athlete_names[0] if show_acwr and athlete_names else None
        logs = get_all_logs() if show_acwr and acwr_athlete else None

        def _describe(ds: str, prog: dict | None) -> tuple[str, str, str, str]:
            prog = ensure_program_dict(prog)
            tp = safe_str(prog.get("type"))
            cat = TRAIN_TYPES.get(tp, {}).get("category", "rest")
            bg = TYPE_CATEGORY_COLORS.get(cat, "#f1f5f9")
            title_line, spec_line = program_calendar_summary(prog) if prog else ("", "")
            detail = spec_line or ""
            if show_acwr and acwr_athlete and logs is not None:
                v, _ = acwr_status(calc_acwr(logs, acwr_athlete, date.fromisoformat(ds)))
                detail = f"{detail} · ACWR {v}".strip(" · ")
            return title_line or "—", detail, tp or "休息", bg

        selected = render_month_day_list(
            year=year,
            month=month,
            select_key=select_key,
            prog_map=prog_map,
            describe_day=_describe,
            pick_mode="copy" if copy_mode else ("delete" if delete_mode else None),
            pick_key="copy_target_dates" if copy_mode else "delete_target_dates",
            copy_source=copy_source,
            empty_label="休息",
            can_pick=(lambda ds, _p: ds in prog_map) if delete_mode else None,
        )
    else:
        selected = _render_calendar_grid(
            select_key, year, month, prog_map, show_acwr,
            copy_mode, delete_mode, copy_source, copy_targets, delete_targets,
        )

    if copy_mode:
        src_payload = st.session_state.get("copy_source_payload")
        if isinstance(src_payload, list) and src_payload:
            src_title = f"{len(src_payload)} 組課表"
            src_spec = "、".join(short_group_label(p.get("group")) for p in src_payload[:4])
        else:
            src_prog = ensure_program_dict(src_payload)
            src_title, src_spec = program_calendar_summary(src_prog) if src_prog else ("", "")
        targets = st.session_state.get("copy_target_dates", [])
        target_text = "、".join(targets) if targets else "（尚未選擇）"
        st.warning(
            f"📋 **複製模式** — 來源：**{copy_source}** {src_title} {src_spec}\n\n"
            f"👉 在月曆上**點選多個目標日期**（可切換月份），再按「確認複製」\n\n"
            f"已選 **{len(targets)}** 日：{target_text}"
        )
    elif delete_mode:
        targets = st.session_state.get("delete_target_dates", [])
        target_text = "、".join(targets) if targets else "（尚未選擇）"
        st.error(
            f"🗑 **多選刪除模式** — 在月曆上點選**有課表的日期**（可跨月），再按「確認刪除」\n\n"
            f"已選 **{len(targets)}** 日：{target_text}"
        )
    else:
        st.info(f"已選日期：**{st.session_state[select_key]}**")
    return selected
