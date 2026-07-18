"""Coach — training timetable calendar (time & venue, per group)."""

from datetime import date

import streamlit as st

from utils.config import GROUP_OPTIONS, SPECIALTY_OPTIONS, VENUE_OPTIONS, group_display_label, normalize_train_type, schedule_placeholder_program
from utils.data_store import (
    apply_time_venue_to_dates,
    build_coach_prog_map,
    build_day_programs_map,
    copy_time_venue_to_dates,
    days_until_competition,
    ensure_program_dict,
    get_programs_for_date,
    get_programs_for_month,
    has_schedule_slot,
    load_periodization,
    save_program,
    save_program_time_venue,
)
from utils.helpers import (
    day_sync_status,
    format_timetable_date,
    format_time_venue_line,
    safe_str,
    short_group_label,
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
    st.session_state.pop("sched_copy_group", None)
    st.session_state.sched_pick_dates = []


def _clear_sched_picks() -> None:
    st.session_state.sched_pick_dates = []


def _day_groups(day_programs: list[dict]) -> list[str]:
    seen: list[str] = []
    for p in day_programs:
        g = safe_str(p.get("group"))
        if g and g not in seen:
            seen.append(g)
    return seen


def _pick_edit_group(sk: str, day_programs: list[dict]) -> str:
    existing = _day_groups(day_programs)
    if existing:
        if len(existing) == 1:
            return existing[0]
        labels = [group_display_label(g) for g in existing]
        idx = st.radio(
            "選擇組別",
            range(len(existing)),
            format_func=lambda i: labels[i],
            horizontal=True,
            key=f"sched_grp_pick_{sk}",
        )
        return existing[idx]
    return st.selectbox(
        "組別",
        GROUP_OPTIONS,
        format_func=group_display_label,
        key=f"sched_grp_new_{sk}",
    )


@st.fragment
def _render_sched_pick_ui(pick_mode: str) -> None:
    copy_source = st.session_state.get("sched_copy_source", "")
    copy_group = st.session_state.get("sched_copy_group", "")
    if pick_mode == "copy" and copy_group:
        st.caption(f"複製 **{group_display_label(copy_group)}** 的時間地點")

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
                disabled=not targets or not copy_group,
                key="sched_copy_confirm",
                use_container_width=True,
            ):
                n = copy_time_venue_to_dates(copy_source, targets, group=copy_group)
                _clear_pick_state()
                st.session_state["sched_flash"] = ("success", f"已複製 {group_display_label(copy_group)} 時間地點至 {n} 日")
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
        bulk_group = st.selectbox(
            "組別",
            GROUP_OPTIONS,
            format_func=group_display_label,
            key="sched_bulk_group",
        )
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
                    targets, bulk_start, bulk_end, bulk_venue, bulk_other, group=bulk_group,
                )
                _clear_pick_state()
                st.session_state["sched_flash"] = (
                    "success",
                    f"已套用 {group_display_label(bulk_group)} 至 {n} 個日期",
                )
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

    st.markdown("#### 編輯當日時間與地點（依組別）")
    edit_group = _pick_edit_group(sk, day_programs)
    st.session_state.sched_edit_group = edit_group
    prog = ensure_program_dict(
        next((p for p in day_programs if safe_str(p.get("group")) == edit_group), None)
        or (day_programs[0] if day_programs else schedule_placeholder_program(sk, group=edit_group))
    )

    sync = day_sync_status(prog if day_programs else None)
    hint = sync_status_label(sync)
    if hint and sync not in ("rest", "empty", "complete"):
        st.caption(hint)

    wdetail = workout_detail(prog) if day_programs else ""
    if wdetail:
        st.markdown("**週期化課表跑案（預覽）**")
        st.markdown(wdetail)
    elif sync in ("need_workout", "need_both") or not day_programs:
        st.warning("此組別尚未在「週期化課表」填寫跑案，可先預排時間地點。")

    if len(day_programs) > 1:
        st.caption(
            f"📅 當日 **{len(day_programs)}** 組訓練 · "
            f"目前編輯：**{group_display_label(edit_group)}**（各組時間地點分開設定）"
        )
    else:
        st.markdown(f"**{format_timetable_date(sk)}** · 👥 **{group_display_label(edit_group)}**")

    available = [g for g in GROUP_OPTIONS if g not in _day_groups(day_programs)]
    if available:
        with st.expander("➕ 新增組別訓練時段", expanded=False):
            new_group = st.selectbox(
                "組別",
                available,
                format_func=group_display_label,
                key=f"sched_add_grp_{sk}",
            )
            if st.button("新增", key=f"sched_add_btn_{sk}", use_container_width=True):
                draft = schedule_placeholder_program(sk, group=new_group)
                save_program(draft)
                st.success(f"已新增 {group_display_label(new_group)} 時段")
                st.rerun()

    rk = f"{sk.replace('-', '')}_{edit_group}"
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
        save_program_time_venue(
            sk, start_time, end_time, venue, venue_other, group=edit_group,
        )
        st.session_state["sched_flash"] = (
            "success",
            f"已儲存 {format_timetable_date(sk)} · {group_display_label(edit_group)}",
        )
        st.rerun()

    b1, b2 = st.columns(2)
    with b1:
        if st.button("📋 複製時間地點到其他日期", key="sched_copy_btn", use_container_width=True):
            grp = st.session_state.get("sched_edit_group", edit_group)
            if not has_schedule_slot(sk, grp):
                st.session_state["sched_flash"] = (
                    "error",
                    f"請先儲存 {group_display_label(grp)} 的時間地點",
                )
                st.rerun()
            st.session_state.sched_pick_mode = "copy"
            st.session_state.sched_copy_source = sk
            st.session_state.sched_copy_group = grp
            st.session_state.sched_pick_dates = []
            st.rerun()
    with b2:
        if st.button("✅ 多選套用時間地點", key="sched_bulk_btn", use_container_width=True):
            st.session_state.sched_pick_mode = "bulk"
            st.session_state.pop("sched_copy_source", None)
            st.session_state.pop("sched_copy_group", None)
            st.session_state.sched_pick_dates = []
            st.rerun()


def render_coach_schedule() -> None:
    st.subheader("📆 訓練時間表")
    st.caption(
        "同一日可為**不同組別**排不同時間地點（1天多練）；"
        "總跑量與跑案在「週期化課表」**依組別**分開計算。"
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
            "💡 選組別 → 填時間地點 → 儲存 · "
            "複製/多選套用會針對**所選組別**操作"
        )
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
