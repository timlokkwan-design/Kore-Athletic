"""Coach — training timetable calendar (time & venue)."""

from datetime import date

import streamlit as st

from utils.config import SPECIALTY_OPTIONS, VENUE_OPTIONS, normalize_train_type
from utils.data_store import (
    apply_time_venue_to_dates,
    copy_time_venue_to_dates,
    days_until_competition,
    ensure_program_dict,
    get_program,
    is_training_day,
    load_periodization,
    save_program_time_venue,
)
from utils.helpers import format_timetable_date, safe_str
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
                st.session_state["sched_flash"] = ("success", f"已複製時間地點至 {n} 個訓練日")
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
        st.markdown("#### 套用到已選日期")
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
                st.session_state["sched_flash"] = ("success", f"已套用至 {n} 個訓練日")
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

    b1, b2 = st.columns(2)
    with b1:
        if st.button("📋 複製時間地點到其他日期", key="sched_copy_btn", use_container_width=True):
            if not is_training_day(sk):
                st.session_state["sched_flash"] = ("error", "請先選有訓練課表的日期作為來源")
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

    st.markdown("#### 編輯當日時間與地點")
    prog = ensure_program_dict(get_program(selected))
    tp = normalize_train_type(safe_str(prog.get("type")))
    if not is_training_day(sk):
        st.info(f"**{format_timetable_date(sk)}** — 休息日，無需設定時間地點。")
    else:
        st.markdown(
            f"**{format_timetable_date(sk)}** · {tp} · "
            f"{safe_str(prog.get('title')) or tp} · 👥 {safe_str(prog.get('group'))}"
        )
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
            st.session_state["sched_flash"] = ("success", f"已儲存 {format_timetable_date(sk)}")
            st.rerun()


def render_coach_schedule() -> None:
    st.subheader("📆 訓練時間表")
    st.caption(
        "月曆顯示**週期化課表**已有訓練；無課表日期顯示**休息**。"
        "此頁只需設定**時間與地點**。"
    )

    pick_mode = st.session_state.get("sched_pick_mode")
    flash = st.session_state.pop("sched_flash", None)
    if flash:
        kind, msg = flash
        (st.success if kind == "success" else st.error)(msg)

    per = load_periodization()
    c1, c2, c3 = st.columns(3)
    c1.metric("訓練階段", per.get("global_phase", "—"))
    c2.metric("本週主題", per.get("global_week_theme", "—"))
    countdown = days_until_competition()
    c3.metric("校際賽倒數", f"{countdown} 天" if countdown is not None else "—")

    if not pick_mode:
        st.caption(
            "💡 **複製**：選日期 →「複製時間地點」→ 多選目標 → 確認 · "
            "**多選套用**：「多選套用時間地點」→ 多選日期 → 填寫 → 確認"
        )

    if pick_mode:
        _render_sched_pick_ui(pick_mode)
    else:
        _render_sched_editor_ui()

    st.divider()
    st.markdown("#### 👀 預覽（學生時間表）")
    preview_group = st.selectbox("模擬學生專項", SPECIALTY_OPTIONS, key="sched_preview_spec")
    render_program_timetable(student_specialty=preview_group, days_ahead=60)
