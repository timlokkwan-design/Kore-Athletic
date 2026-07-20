"""Coach — training timetable calendar (unified time & venue for all groups)."""
from datetime import date, time as dt_time

import streamlit as st

from utils.config import SPECIALTY_OPTIONS, VENUE_OPTIONS, schedule_placeholder_program
from utils.data_store import (
    apply_time_venue_to_dates,
    build_coach_prog_map,
    clear_program_time_venue,
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
from utils.coach_calendar_state import set_coach_calendar_date, get_coach_calendar_year_month
from views.components.coach_sync import _goto_program_edit, render_month_sync_alerts
from views.components.schedule import render_program_timetable
from views.components.schedule_calendar import render_schedule_calendar

_DEFAULT_START = dt_time(17, 0)
_DEFAULT_END = dt_time(19, 0)
_TIME_PRESETS = [
    ("17:00–19:00", dt_time(17, 0), dt_time(19, 0)),
    ("16:00–18:00", dt_time(16, 0), dt_time(18, 0)),
    ("18:00–20:00", dt_time(18, 0), dt_time(20, 0)),
]


def _parse_hhmm(raw: str, default: dt_time = _DEFAULT_START) -> dt_time:
    text = safe_str(raw).strip()
    if not text:
        return default
    try:
        parts = text.replace(".", ":").split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return dt_time(h % 24, m % 60)
    except (ValueError, IndexError, TypeError):
        return default


def _fmt_hhmm(value: dt_time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}"


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


def _render_time_presets(start_key: str, end_key: str, *, key_prefix: str) -> None:
    st.caption("快速時段")
    cols = st.columns(len(_TIME_PRESETS))
    for col, (label, start, end) in zip(cols, _TIME_PRESETS):
        with col:
            if st.button(label, key=f"{key_prefix}_{label}", use_container_width=True):
                st.session_state[start_key] = start
                st.session_state[end_key] = end
                st.rerun()


@st.fragment
def _render_sched_pick_ui(pick_mode: str) -> None:
    copy_source = st.session_state.get("sched_copy_source", "")

    render_schedule_calendar(
        "coach_cal",
        pick_mode=pick_mode,
        pick_key="sched_pick_dates",
        copy_source=copy_source if pick_mode == "copy" else "",
    )

    from views.components.coach_mobile_ui import force_button_row

    if pick_mode == "copy":
        targets = st.session_state.get("sched_pick_dates", [])
        with force_button_row(key="sched_copy_actions", n_cols=3) as cols:
            b1, b2, b3 = cols
            with b1:
                if st.button(
                    f"✅ 複製 {len(targets)}",
                    type="primary",
                    disabled=not targets,
                    key="sched_copy_confirm",
                    use_container_width=True,
                ):
                    n = copy_time_venue_to_dates(copy_source, targets)
                    _clear_pick_state()
                    st.session_state["sched_flash"] = ("success", f"已複製全隊時間地點至 {n} 日")
                    if targets:
                        set_coach_calendar_date(targets[-1])
                    st.rerun()
            with b2:
                st.button(
                    "↺ 清除",
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
        _render_time_presets("sched_bulk_st", "sched_bulk_et", key_prefix="sched_bulk_preset")
        if "sched_bulk_st" not in st.session_state:
            st.session_state.sched_bulk_st = _DEFAULT_START
        if "sched_bulk_et" not in st.session_state:
            st.session_state.sched_bulk_et = _DEFAULT_END
        bulk_start = st.time_input("開始時間", key="sched_bulk_st")
        bulk_end = st.time_input("結束時間", key="sched_bulk_et")
        bulk_venue = st.selectbox("地點", VENUE_OPTIONS, key="sched_bulk_vn")
        bulk_other = ""
        if bulk_venue == "其他":
            bulk_other = st.text_input("其他地點", key="sched_bulk_vo", placeholder="請填寫詳細地點")
        with force_button_row(key="sched_bulk_actions", n_cols=3) as cols:
            b1, b2, b3 = cols
            with b1:
                if st.button(
                    f"✅ 套用 {len(targets)}",
                    type="primary",
                    disabled=not targets,
                    key="sched_bulk_confirm",
                    use_container_width=True,
                ):
                    n = apply_time_venue_to_dates(
                        targets,
                        _fmt_hhmm(bulk_start),
                        _fmt_hhmm(bulk_end),
                        bulk_venue,
                        bulk_other,
                    )
                    _clear_pick_state()
                    st.session_state["sched_flash"] = ("success", f"已套用全隊時間地點至 {n} 個日期")
                    st.rerun()
            with b2:
                st.button(
                    "↺ 清除",
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
    selected = render_schedule_calendar("coach_cal", pick_mode=None)
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

    start_key = f"sched_st_{rk}"
    end_key = f"sched_et_{rk}"
    if start_key not in st.session_state:
        st.session_state[start_key] = _parse_hhmm(safe_str(prog.get("start_time")), _DEFAULT_START)
    if end_key not in st.session_state:
        st.session_state[end_key] = _parse_hhmm(safe_str(prog.get("end_time")), _DEFAULT_END)

    _render_time_presets(start_key, end_key, key_prefix=f"sched_preset_{rk}")
    start_time = st.time_input("開始", key=start_key)
    end_time = st.time_input("結束", key=end_key)
    venue = st.selectbox("地點", VENUE_OPTIONS, index=venue_idx, key=f"sched_vn_{rk}")
    venue_other = ""
    if venue == "其他":
        venue_other = st.text_input(
            "其他地點", safe_str(prog.get("venue_other")),
            placeholder="請填寫詳細地點", key=f"sched_vo_{rk}",
        )
    if st.button("💾 儲存時間與地點", type="primary", key=f"sched_save_{rk}", use_container_width=True):
        save_program_time_venue(
            sk, _fmt_hhmm(start_time), _fmt_hhmm(end_time), venue, venue_other,
        )
        st.session_state["sched_flash"] = (
            "success",
            f"已儲存 {format_timetable_date(sk)} 全隊時間地點",
        )
        st.rerun()

    if st.button(
        "✏️ 前往設定此日跑案",
        key=f"sched_goto_prog_{rk}",
        use_container_width=True,
    ):
        _goto_program_edit(sk)
        st.rerun()

    has_slot = has_schedule_slot(sk)
    clear_confirm_key = f"sched_clear_confirm_{rk}"
    from views.components.coach_mobile_ui import force_button_row

    # 取消｜複製｜多選 — one compact row (was 2 stacked strips)
    with force_button_row(key=f"sched_tools_row_{rk}", n_cols=3) as cols:
        a1, b1, b2 = cols
        with a1:
            if st.button(
                "🗑 取消",
                key=f"sched_clear_{rk}",
                use_container_width=True,
                disabled=not has_slot,
                help="清除此日已設定的開始／結束時間與地點（全隊同步）",
            ):
                st.session_state[clear_confirm_key] = True
                st.rerun()
        with b1:
            if st.button("📋 複製", key="sched_copy_btn", use_container_width=True):
                if not has_schedule_slot(sk):
                    st.session_state["sched_flash"] = ("error", "請先儲存此日的時間地點")
                    st.rerun()
                st.session_state.sched_pick_mode = "copy"
                st.session_state.sched_copy_source = sk
                st.session_state.sched_pick_dates = []
                st.rerun()
        with b2:
            if st.button("✅ 多選", key="sched_bulk_btn", use_container_width=True):
                st.session_state.sched_pick_mode = "bulk"
                st.session_state.pop("sched_copy_source", None)
                st.session_state.sched_pick_dates = []
                st.rerun()

    if st.session_state.get(clear_confirm_key):
        st.warning(f"確認清除 **{format_timetable_date(sk)}** 的訓練時間與地點？")
        if st.button(
            "確認清除",
            key=f"sched_clear_yes_{rk}",
            type="primary",
            use_container_width=True,
        ):
            if clear_program_time_venue(sk):
                for suffix in ("st", "et", "vn", "vo"):
                    st.session_state.pop(f"sched_{suffix}_{rk}", None)
                st.session_state["sched_flash"] = (
                    "success",
                    f"已取消 {format_timetable_date(sk)} 的訓練時間與地點",
                )
            else:
                st.session_state["sched_flash"] = ("error", "此日沒有可取消的時間地點")
            st.session_state.pop(clear_confirm_key, None)
            st.rerun()
        if st.button("返回", key=f"sched_clear_no_{rk}", use_container_width=True):
            st.session_state.pop(clear_confirm_key, None)
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
        year, month = get_coach_calendar_year_month()
        sched_map = build_coach_prog_map(get_programs_for_month(year, month))
        render_month_sync_alerts(sched_map, page="sched")

    if pick_mode:
        _render_sched_pick_ui(pick_mode)
    else:
        _render_sched_editor_ui()

    st.divider()
    st.markdown("#### 👀 預覽（學生時間表列表）")
    st.caption("完整日曆檢視請用上方「課表檢視」。")
    from views.components.coach_mobile_ui import render_option_chips

    preview_group = render_option_chips(
        key="sched_preview_spec_chips",
        options=list(SPECIALTY_OPTIONS),
        session_key="sched_preview_spec",
        caption="模擬學生專項",
        per_row=3,
    )
    render_program_timetable(student_specialty=preview_group, days_ahead=60)
