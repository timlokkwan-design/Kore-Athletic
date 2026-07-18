"""V6-style month calendar grid."""

import calendar
from datetime import date

import streamlit as st

from utils.acwr import acwr_status, calc_acwr
from utils.config import TRAIN_TYPES, TYPE_CATEGORY_COLORS
from utils.data_store import (
    ensure_program_dict,
    get_all_logs,
    get_programs_for_month,
    get_student_names,
    row_to_program,
)
from utils.helpers import normalize_date_str, program_calendar_summary, safe_str


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


def render_calendar(select_key: str = "cal_select", show_acwr: bool = False, copy_mode: bool = False) -> date | None:
    if "cal_year" not in st.session_state:
        t = date.today()
        st.session_state.cal_year, st.session_state.cal_month = t.year, t.month

    copy_source = st.session_state.get("copy_source_date", "") if copy_mode else ""
    copy_targets = set(st.session_state.get("copy_target_dates", [])) if copy_mode else set()

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 上月", key=f"{select_key}_prev"):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month, st.session_state.cal_year = 12, st.session_state.cal_year - 1
        else:
            st.session_state.cal_month -= 1
        if not copy_mode:
            _sync_selection_to_month(select_key, st.session_state.cal_year, st.session_state.cal_month)
        st.rerun()
    c2.markdown(f"### {st.session_state.cal_year} 年 {st.session_state.cal_month:02d} 月")
    if c3.button("下月 ▶", key=f"{select_key}_next"):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month, st.session_state.cal_year = 1, st.session_state.cal_year + 1
        else:
            st.session_state.cal_month += 1
        if not copy_mode:
            _sync_selection_to_month(select_key, st.session_state.cal_year, st.session_state.cal_month)
        st.rerun()

    if copy_mode:
        st.caption("🟧 橙色=來源 · 🟩 綠色=已選目標（可跨月多選）· 點一下選取/取消")
    else:
        st.caption("🟥速度 🟦耐力 🟪技術 🟧肌力 🟩比賽 ⬜休息")

    year, month = st.session_state.cal_year, st.session_state.cal_month
    if not copy_mode:
        _sync_selection_to_month(select_key, year, month)
    programs = get_programs_for_month(year, month)
    prog_map: dict[str, dict] = {}
    if not programs.empty:
        for _, row in programs.iterrows():
            ds = normalize_date_str(row.get("date"))
            if ds:
                prog_map[ds] = row_to_program(row)

    if select_key not in st.session_state:
        st.session_state[select_key] = date.today().isoformat()

    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    hdr = st.columns(7)
    for i, w in enumerate(weekdays):
        hdr[i].markdown(f"**{w}**")

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    logs = get_all_logs()
    athlete_names = get_student_names()
    acwr_athlete = athlete_names[0] if show_acwr and athlete_names else None

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
            active = (not copy_mode) and st.session_state[select_key] == ds
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
            elif active:
                border = "3px solid #1d4ed8"
                weight = "bold"
            else:
                border = "1px solid #e2e8f0"
                weight = "normal"
            title_line, spec_line = program_calendar_summary(prog) if prog else ("", "")
            acwr_html = ""
            if show_acwr and acwr_athlete and not copy_mode:
                v, _ = acwr_status(calc_acwr(logs, acwr_athlete, date.fromisoformat(ds)))
                acwr_html = f"<br><small style='color:#64748b;'>ACWR {v}</small>"
            btn_label = f"{day}"
            if tp and not copy_mode:
                btn_label = f"{day} · {tp[:2]}"
            if copy_mode and ds != copy_source:
                btn_label = f"✓ {day}" if ds in copy_targets else f"+ {day}"
            if cols[i].button(btn_label, key=f"{select_key}_{ds}", use_container_width=True):
                if copy_mode:
                    _toggle_copy_target(ds, copy_source)
                    st.rerun()
                else:
                    st.session_state[select_key] = ds
                    st.rerun()
            spec_html = f"<br><span style='color:#475569;'>{spec_line}</span>" if spec_line else ""
            cols[i].markdown(
                f"<div style='background:{bg};border:{border};border-radius:4px;padding:3px 4px;"
                f"min-height:44px;font-size:10px;line-height:1.25;margin-top:-6px;font-weight:{weight};'>"
                f"<span style='color:#1e3a8a;font-weight:600;'>{title_line or '—'}</span>"
                f"{spec_html}{acwr_html}</div>",
                unsafe_allow_html=True,
            )

    selected = date.fromisoformat(st.session_state[select_key])
    if copy_mode:
        src_prog = ensure_program_dict(st.session_state.get("copy_source_payload"))
        src_title, src_spec = program_calendar_summary(src_prog) if src_prog else ("", "")
        targets = st.session_state.get("copy_target_dates", [])
        target_text = "、".join(targets) if targets else "（尚未選擇）"
        st.warning(
            f"📋 **複製模式** — 來源：**{copy_source}** {src_title} {src_spec}\n\n"
            f"👉 在月曆上**點選多個目標日期**（可切換月份），再按「確認複製」\n\n"
            f"已選 **{len(targets)}** 日：{target_text}"
        )
    else:
        st.info(f"已選日期：**{st.session_state[select_key]}**")
    return selected
