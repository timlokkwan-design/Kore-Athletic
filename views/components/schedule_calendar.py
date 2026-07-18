"""Month calendar for coach training timetable (time & venue)."""

import calendar
from datetime import date

import streamlit as st

from utils.config import TRAIN_TYPES, TYPE_CATEGORY_COLORS, normalize_train_type
from utils.data_store import get_programs_for_month, is_training_day, row_to_program
from utils.helpers import normalize_date_str, program_calendar_summary, resolve_venue, safe_str


def _sync_sched_month(select_key: str, year: int, month: int) -> None:
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


def _toggle_pick(ds: str, pick_key: str, source: str = "", *, block_source: bool = False) -> None:
    if block_source and ds == source:
        st.session_state["sched_flash"] = ("error", "來源日期不能選為目標")
        return
    picks = list(st.session_state.get(pick_key, []))
    if ds in picks:
        picks.remove(ds)
    else:
        picks.append(ds)
    st.session_state[pick_key] = sorted(picks)


def _cell_summary(prog: dict | None) -> tuple[str, str, str]:
    """Return (title_line, detail_line, train_type) for calendar cell."""
    if not prog:
        return "休息", "", "休息"
    tp = normalize_train_type(safe_str(prog.get("type")))
    if tp == "休息":
        return "休息", "", "休息"
    title, spec = program_calendar_summary(prog)
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    time_part = f"{start}–{end}" if start and end else (start or end or "")
    venue = resolve_venue(prog)
    if venue == "（待設定）":
        venue = ""
    parts = [p for p in (time_part, venue) if p]
    detail = " · ".join(parts)
    return title or tp, detail, tp


def render_schedule_calendar(
    select_key: str = "sched_cal",
    *,
    pick_mode: str | None = None,
    pick_key: str = "sched_pick_dates",
    copy_source: str = "",
) -> date:
    """
    pick_mode: None | 'copy' | 'bulk'
    """
    if "sched_cal_year" not in st.session_state:
        t = date.today()
        st.session_state.sched_cal_year, st.session_state.sched_cal_month = t.year, t.month

    picks = set(st.session_state.get(pick_key, []))

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 上月", key=f"{select_key}_prev"):
        if st.session_state.sched_cal_month == 1:
            st.session_state.sched_cal_month, st.session_state.sched_cal_year = 12, st.session_state.sched_cal_year - 1
        else:
            st.session_state.sched_cal_month -= 1
        if not pick_mode:
            _sync_sched_month(select_key, st.session_state.sched_cal_year, st.session_state.sched_cal_month)
        st.rerun()
    c2.markdown(f"### {st.session_state.sched_cal_year} 年 {st.session_state.sched_cal_month:02d} 月")
    if c3.button("下月 ▶", key=f"{select_key}_next"):
        if st.session_state.sched_cal_month == 12:
            st.session_state.sched_cal_month, st.session_state.sched_cal_year = 1, st.session_state.sched_cal_year + 1
        else:
            st.session_state.sched_cal_month += 1
        if not pick_mode:
            _sync_sched_month(select_key, st.session_state.sched_cal_year, st.session_state.sched_cal_month)
        st.rerun()

    if pick_mode == "copy":
        st.caption("🟧 橙色=來源 · 🟩 綠色=已選目標 · 僅訓練日可複製")
    elif pick_mode == "bulk":
        st.caption("🟩 綠色=已選 · 點一下選取/取消 · 僅訓練日可套用")
    else:
        st.caption("有課表=訓練日 · 空白=休息 · 🟥速度 🟦耐力 🟪技術 🟧肌力 🟩比賽")

    year, month = st.session_state.sched_cal_year, st.session_state.sched_cal_month
    if not pick_mode:
        _sync_sched_month(select_key, year, month)

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

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown(
                    "<div style='min-height:78px;background:#f8fafc;border-radius:4px;'></div>",
                    unsafe_allow_html=True,
                )
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            prog = prog_map.get(ds)
            title_line, detail_line, tp = _cell_summary(prog)
            cat = TRAIN_TYPES.get(tp, {}).get("category", "rest")
            bg = TYPE_CATEGORY_COLORS.get(cat, "#f1f5f9")
            training = is_training_day(ds)

            active = (not pick_mode) and st.session_state[select_key] == ds
            if pick_mode == "copy" and ds == copy_source:
                border, weight = "3px solid #f59e0b", "bold"
            elif pick_mode and ds in picks:
                border, weight = "3px solid #16a34a", "bold"
                if pick_mode:
                    bg = "#dcfce7"
            elif pick_mode and training:
                border, weight = "2px dashed #86efac", "normal"
            elif active:
                border, weight = "3px solid #1d4ed8", "bold"
            else:
                border, weight = "1px solid #e2e8f0", "normal"

            btn_label = str(day)
            if pick_mode and training and ds != copy_source:
                btn_label = f"✓ {day}" if ds in picks else f"+ {day}"
            elif not pick_mode and tp != "休息":
                btn_label = f"{day} · {tp[:2]}"

            if cols[i].button(btn_label, key=f"{select_key}_{ds}", use_container_width=True):
                if pick_mode:
                    if training:
                        _toggle_pick(
                            ds, pick_key, copy_source,
                            block_source=(pick_mode == "copy"),
                        )
                    st.rerun()
                else:
                    st.session_state[select_key] = ds
                    st.rerun()

            detail_html = f"<br><span style='color:#64748b;'>{detail_line}</span>" if detail_line else ""
            cols[i].markdown(
                f"<div style='background:{bg};border:{border};border-radius:4px;padding:3px 4px;"
                f"min-height:48px;font-size:10px;line-height:1.25;margin-top:-6px;font-weight:{weight};'>"
                f"<span style='color:#1e3a8a;font-weight:600;'>{title_line}</span>"
                f"{detail_html}</div>",
                unsafe_allow_html=True,
            )

    selected = date.fromisoformat(st.session_state[select_key])
    picks_list = st.session_state.get(pick_key, [])

    if pick_mode == "copy":
        src_prog = prog_map.get(copy_source) or {}
        src_title, _, _ = _cell_summary(src_prog)
        st.warning(
            f"📋 **複製時間地點** — 來源：**{copy_source}** {src_title}\n\n"
            f"👉 多選訓練日後按「確認複製」\n\n"
            f"已選 **{len(picks_list)}** 日：{('、'.join(picks_list) if picks_list else '（尚未選擇）')}"
        )
    elif pick_mode == "bulk":
        st.warning(
            f"✅ **多選套用** — 已選 **{len(picks_list)}** 日："
            f"{('、'.join(picks_list) if picks_list else '（請在月曆點選訓練日）')}"
        )
    else:
        st.info(f"已選日期：**{st.session_state[select_key]}**")

    return selected
