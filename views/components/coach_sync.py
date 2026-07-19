"""Coach alerts when 設定課表 and 訓練時間表 are out of sync."""

from __future__ import annotations

from utils.coach_calendar_state import set_coach_calendar_date
from utils.helpers import day_sync_status, format_timetable_date


def _goto_program_edit(ds: str) -> None:
    """Jump straight into 設定課表 day editor for this date."""
    import streamlit as st

    set_coach_calendar_date(ds)
    st.session_state["main_page"] = "教練平台"
    st.session_state["coach_section"] = "設定課表"
    st.session_state["coach_prog_screen"] = "edit"
    st.session_state["copy_mode"] = False
    st.session_state["delete_mode"] = False
    st.session_state.pop("sched_pick_mode", None)


def _goto_schedule_edit(ds: str) -> None:
    """Jump to 訓練時間表 focused on this date."""
    import streamlit as st

    set_coach_calendar_date(ds)
    st.session_state["main_page"] = "教練平台"
    st.session_state["coach_section"] = "訓練時間表"
    st.session_state.pop("sched_pick_mode", None)


def _render_date_action_row(
    dates: list[str],
    *,
    key_prefix: str,
    on_pick,
    limit: int = 8,
) -> None:
    """Compact tappable date chips — one tap → edit (via on_click, no extra delay)."""
    import streamlit as st

    if not dates:
        return
    shown = dates[:limit]
    st.caption("👉 點日期即時進入編輯")
    # Rows of up to 3 chips so mobile keeps them side-by-side
    for row_i in range(0, len(shown), 3):
        chunk = shown[row_i : row_i + 3]
        with st.container():
            st.markdown(
                '<div class="ka-inline-row-marker"></div>',
                unsafe_allow_html=True,
            )
            cols = st.columns(len(chunk), gap="small")
            for col, ds in zip(cols, chunk):
                with col:
                    st.button(
                        format_timetable_date(ds),
                        key=f"{key_prefix}_{ds}",
                        use_container_width=True,
                        type="primary",
                        on_click=on_pick,
                        args=(ds,),
                    )
    if len(dates) > limit:
        st.caption(f"另有 {len(dates) - limit} 日未列出 · 可在月曆點選")


def render_month_sync_alerts(prog_map: dict[str, dict], *, page: str) -> None:
    """page: 'prog' (設定課表) or 'sched' (訓練時間表)."""
    import streamlit as st

    need_workout: list[str] = []
    need_schedule: list[str] = []
    for ds in sorted(prog_map.keys()):
        status = day_sync_status(prog_map.get(ds))
        if status == "need_workout":
            need_workout.append(ds)
        elif status == "need_schedule":
            need_schedule.append(ds)

    if page == "prog":
        if need_workout:
            st.warning("📌 **訓練時間表已設定時間**，以下日期待寫跑案（點日期即編輯）：")
            _render_date_action_row(
                need_workout,
                key_prefix="sync_prog_wo",
                on_pick=_goto_program_edit,
            )
        if need_schedule:
            st.info("📌 以下日期**跑案已寫**，請至「訓練時間表」填時間地點（點日期即前往）：")
            _render_date_action_row(
                need_schedule,
                key_prefix="sync_prog_sc",
                on_pick=_goto_schedule_edit,
            )
    else:
        if need_workout:
            st.info("📌 以下日期**時間已定**，請至「設定課表」填寫跑案（點日期即編輯）：")
            _render_date_action_row(
                need_workout,
                key_prefix="sync_sched_wo",
                on_pick=_goto_program_edit,
            )
        if need_schedule:
            st.warning("📌 **設定課表已有跑案**，以下日期待填時間地點（點日期即編輯）：")
            _render_date_action_row(
                need_schedule,
                key_prefix="sync_sched_sc",
                on_pick=_goto_schedule_edit,
            )
