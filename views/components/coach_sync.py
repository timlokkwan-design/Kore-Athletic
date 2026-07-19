"""Coach alerts when 週期化課表 and 訓練時間表 are out of sync."""

from __future__ import annotations

from utils.helpers import day_sync_status, format_timetable_date


def _fmt_days(dates: list[str], limit: int = 6) -> str:
    if not dates:
        return ""
    shown = [format_timetable_date(d) for d in dates[:limit]]
    text = "、".join(shown)
    if len(dates) > limit:
        text += f" 等 {len(dates)} 日"
    return text


def render_month_sync_alerts(prog_map: dict[str, dict], *, page: str) -> None:
    """page: 'prog' (週期化課表) or 'sched' (訓練時間表)."""
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
            st.warning(
                f"📌 **訓練時間表已設定時間**，以下日期待寫跑案：{_fmt_days(need_workout)}"
            )
        if need_schedule:
            st.info(
                f"📌 以下日期**跑案已寫**，請至「訓練時間表」填時間地點：{_fmt_days(need_schedule)}"
            )
    else:
        if need_workout:
            st.info(
                f"📌 以下日期**時間已定**，請至「設定課表」填寫跑案：{_fmt_days(need_workout)}"
            )
        if need_schedule:
            st.warning(
                f"📌 **設定課表已有跑案**，以下日期待填時間地點：{_fmt_days(need_schedule)}"
            )
