"""Coach — training timetable calendar (unified time & venue for all groups)."""
from datetime import date

import streamlit as st

from utils.config import SPECIALTY_OPTIONS, VENUE_OPTIONS, schedule_placeholder_program
from utils.data_store import (
    apply_time_venue_to_dates,
    build_coach_prog_map,
    copy_time_venue_to_dates,
    days_until_competition,
    ensure_program_dict,
    get_programs_for_date,
    get_programs_for_month,
    has_schedule_slot,
    save_program_time_venue,
)
from utils.helpers import (
    day_sync_status,
    format_time_venue_line,
    format_timetable_date,
    has_time_venue,
    safe_str,
    sync_status_label,
    workout_detail,
)
from views.components.coach_sync import render_month_sync_alerts
from views.components.schedule import render_program_timetable
from views.components.schedule_calendar import render_schedule_calendar


def _select_index(options: list, value, default: int = 0) -> int:
    if not options:
        return 0
    v = safe_str(value, "")
    if not v or v.lower() in ("nan", "none"):
        return default
    try:
        return options.index(v)
    except ValueError:
        return default


def _clear_pick_state() -> None:
    st.session_state.sched_pick_mode = None
    st.session_state.pop("sched_copy_source", None)
    st.session_state.sched_pick_dates = []


def _clear_sched_picks() -> None:
    st.session_state.sched_pick_dates = []


def _unified_day_prog(day_programs: list[dict], sk: str) -> dict:
    for p in day_programs:
        if has_time_venue(p):
            return ensure_program_dict(p)
    if day_programs:
        return ensure_program_dict(day_programs[0])
    return ensure_program_dict(schedule_placeholder_program(sk, group="全體組員"))


@st.fragment
def _render_sched_pick_ui(pick_mode: str) -> None:
    copy_source = st.session_state.get("sched_copy_source", "")

    render_schedule_calendar(
        "sched_cal",
        pick_mode=pick_mode,
        pick_key="sched_pick_dates",
        copy_source=copy_source if pick_mode == "copy" else "",
    )

    if pick_mode == "copy":
        targets = st.session_state.get("sched_pick_dates", [])
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button(
                f"✅ 確認複製到 {len(targets)} 個日期",
                type="primary",
                disabled=not targets,
                key="sched_copy_confirm",
                use_container_width=True,
            ):
                n = copy_time_venue_to_dates(copy_source, targets)
                _clear_pick_state()
                st.session_state["sched_flash"] = ("success", f"已複製全隊時間地點至 {n} 日")
                if targets:
                    st.session_state["sched_cal"] = targets[-1]
                    d = date.fromisoformat(targets[-1])
                    st.session_state.sched_cal_year = d.year
                    st.session_state.sched_cal_month = d.month
                st.rerun()
        with b2:
            st.button(
                "↺ 清除已選",
                disabled=not targets,
                key="sched_copy_clear",
                use_container_width=True,
                on_click=_clear_sched_picks,
            )
        with b3:
            if st.button("✖ 取消", key="sched_copy_cancel", use_container_width=True):
                _clear_pick_state()
                st.rerun()

    elif pick_mode == "bulk":
        targets = st.session_state.get("sched_pick_dates", [])
        st.markdown("#### 套用到已選日期（全隊同一時間地點）")
        f1, f2, f3 = st.columns(3)
        bulk_start = f1.text_input("開始時間", "17:00", key="sched_bulk_st")
        bulk_end = f2.text_input("結束時間", "19:00", key="sched_bulk_et")
        bulk_venue = f3.selectbox("地點", VENUE_OPTIONS, key="sched_bulk_vn")
        bulk_other = ""
        if bulk_venue == "其他":
            bulk_other = st.text_input("其他地點", key="sched_bulk_vo", placeholder="請填寫詳細地點")
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button(
                f"✅ 套用到 {len(targets)} 個日期",
                type="primary",
                disabled=not targets,
                key="sched_bulk_confirm",
                use_container_width=True,
            ):
                n = apply_time_venue_to_dates(
                    targets, bulk_start, bulk_end, bulk_venue, bulk_other,
                )
                _clear_pick_state()
                st.session_state["sched_flash"] = ("success", f"已套用全隊時間地點至 {n} 個日期")
                st.rerun()
        with b2:
            st.button(
                "↺ 清除已選",
                disabled=not targets,
                key="sched_bulk_clear",
                use_container_width=True,
                on_click=_clear_sched_picks,
            )
        with b3:
            if st.button("✖ 取消", key="sched_bulk_cancel", use_container_width=True):
                _clear_pick_state()
                st.rerun()


@st.fragment
def _render_sched_editor_ui() -> None:
    selected = render_schedule_calendar("sched_cal", pick_mode=None)
    sk = selected.isoformat()
    day_programs = get_programs_for_date(selected)
    prog = _unified_day_prog(day_programs, sk)

    st.markdown("#### 編輯當日時間與地點（全隊共用）")
    st.caption("儲存後 **短跑、中長跑、跨欄、全體組員** 皆使用相同時間與地點。")

    sync = day_sync_status(prog if day_programs else None)
    hint = sync_status_label(sync)
    if hint and sync not in ("rest", "empty", "complete"):
        st.caption(hint)

    wdetail = workout_detail(prog) if day_programs else ""
    if wdetail:
        st.markdown("**設定課表跑案（預覽）**")
        st.markdown(wdetail)
    elif sync in ("need_workout", "need_both") or not day_programs:
        st.warning("此日尚未在「設定課表」填寫跑案，可先預排全隊時間地點。")

    st.markdown(f"**{format_timetable_date(sk)}**")
    tv = format_time_venue_line(prog)
    if tv:
        st.caption(f"目前：{tv}")

    rk = sk.replace("-", "")
    venue_val = safe_str(prog.get("venue"))
    venue_idx = _select_index(VENUE_OPTIONS, venue_val)
    if venue_val and venue_val not in VENUE_OPTIONS:
        venue_idx = VENUE_OPTIONS.index("其他")

    c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
    start_time = c1.text_input(
        "開始時間", safe_str(prog.get("start_time")), placeholder="17:00", key=f"sched_st_{rk}",
    )
    end_time = c2.text_input(
        "結束時間", safe_str(prog.get("end_time")), placeholder="19:00", key=f"sched_et_{rk}",
    )
    venue = c3.selectbox("地點", VENUE_OPTIONS, index=venue_idx, key=f"sched_vn_{rk}")
    venue_other = ""
    if venue == "其他":
        venue_other = c4.text_input(
            "其他地點", safe_str(prog.get("venue_other")),
            placeholder="請填寫詳細地點", key=f"sched_vo_{rk}",
        )
    if st.button("💾 儲存時間與地點", type="primary", key=f"sched_save_{rk}"):
        save_program_time_venue(sk, start_time, end_time, venue, venue_other)
        st.session_state["sched_flash"] = (
            "success",
            f"已儲存 {format_timetable_date(sk)} 全隊時間地點",
        )
        st.rerun()

    b1, b2 = st.columns(2)
    with b1:
        if st.button("📋 複製時間地點到其他日期", key="sched_copy_btn", use_container_width=True):
            if not has_schedule_slot(sk):
                st.session_state["sched_flash"] = ("error", "請先儲存此日的時間地點")
                st.rerun()
            st.session_state.sched_pick_mode = "copy"
            st.session_state.sched_copy_source = sk
            st.session_state.sched_pick_dates = []
            st.rerun()
    with b2:
        if st.button("✅ 多選套用時間地點", key="sched_bulk_btn", use_container_width=True):
            st.session_state.sched_pick_mode = "bulk"
            st.session_state.pop("sched_copy_source", None)
            st.session_state.sched_pick_dates = []
            st.rerun()


def render_coach_schedule() -> None:
    st.subheader("📆 訓練時間表")
    st.caption(
        "全隊共用同一時間與地點；"
        "各組跑案內容仍在「設定課表」**依組別**分開編輯。"
    )

    pick_mode = st.session_state.get("sched_pick_mode")
    flash = st.session_state.pop("sched_flash", None)
    if flash:
        kind, msg = flash
        (st.success if kind == "success" else st.error)(msg)

    countdown = days_until_competition()
    st.metric("校際賽倒數", f"{countdown} 天" if countdown is not None else "—")

    if not pick_mode:
        st.caption("💡 選日期 → 填時間地點 → 儲存（全隊同步）")
        year = st.session_state.get("sched_cal_year", date.today().year)
        month = st.session_state.get("sched_cal_month", date.today().month)
        sched_map = build_coach_prog_map(get_programs_for_month(year, month))
        render_month_sync_alerts(sched_map, page="sched")

    if pick_mode:
        _render_sched_pick_ui(pick_mode)
    else:
        _render_sched_editor_ui()

    st.divider()
    st.markdown("#### 👀 預覽（學生時間表）")
    preview_group = st.selectbox("模擬學生專項", SPECIALTY_OPTIONS, key="sched_preview_spec")
    render_program_timetable(student_specialty=preview_group, days_ahead=60)
