"""Student competition registration — pick events; manual PB only when no record."""
from __future__ import annotations

from datetime import date

import streamlit as st

from utils.data_store import (
    delete_comp_entry,
    ensure_youth_age_group_v_registrations,
    get_best_performance_last_year,
    get_student_competitions,
    resolve_event_pb,
    submit_comp_entry,
)
from utils.helpers import format_birth_display, format_timetable_date, safe_str
from views.components.comp_roster import render_successful_registration_roster


def _profile_complete(user: dict) -> bool:
    return all([
        safe_str(user.get("name")),
        safe_str(user.get("name_en")),
        format_birth_display(user) != "—",
        safe_str(user.get("gender")),
        safe_str(user.get("hkaaa_id")),
        safe_str(user.get("hk_permanent_resident")),
    ])


def _collect_manual_pbs(
    athlete_name: str,
    events: list[str],
    comp_id: str,
    saved_pbs: dict[str, dict],
) -> dict[str, dict]:
    manual: dict[str, dict] = {}
    for event in events:
        auto = get_best_performance_last_year(athlete_name, event)
        if auto.get("score"):
            st.success(
                f"**{event}** — 已有申報成績紀錄：{auto['score']} "
                f"（{auto.get('comp_name') or '—'} · {auto.get('date') or '—'}）"
            )
            continue

        st.markdown(f"**{event}** — 請填寫最佳成績")
        saved = saved_pbs.get(event, {})
        c1, c2, c3 = st.columns(3)
        score = c1.text_input("最佳成績", value=saved.get("score", ""), key=f"pb_score_{comp_id}_{event}")
        comp_name = c2.text_input("賽事", value=saved.get("comp_name", ""), key=f"pb_comp_{comp_id}_{event}")
        default_date = date.today()
        if saved.get("date"):
            try:
                default_date = date.fromisoformat(saved["date"])
            except ValueError:
                pass
        pb_date = c3.date_input("比賽日期", value=default_date, key=f"pb_date_{comp_id}_{event}")
        manual[event] = {
            "score": score.strip(),
            "comp_name": comp_name.strip(),
            "date": pb_date.isoformat(),
        }
    return manual


def _render_comp_signup(user: dict, comp: dict) -> None:
    comp_id = comp["id"]
    athlete_name = user["name"]
    username = user["username"]
    available = comp.get("events") or []
    if not available:
        st.warning("此比賽尚未開放項目。")
        return

    date_label = format_timetable_date(comp["date"]) if comp.get("date") else "—"
    st.markdown(f"**{comp['name']}** · {date_label} · {comp.get('location') or '—'}")
    if comp.get("link"):
        st.markdown(f"🔗 [比賽連結]({comp['link']})")
    if comp.get("deadline"):
        st.caption(f"報名截止：{comp['deadline']}")
    if comp.get("notes"):
        st.info(comp["notes"])

    default_events = comp.get("my_events") or []
    picked = st.multiselect(
        "選擇參賽項目",
        available,
        default=[e for e in default_events if e in available],
        key=f"student_comp_events_{comp_id}",
    )

    saved_pbs = comp.get("my_event_pbs") or {}
    manual_pbs = _collect_manual_pbs(athlete_name, picked, comp_id, saved_pbs) if picked else {}

    c1, c2 = st.columns(2)
    if c1.button("提交報名", type="primary", key=f"student_comp_submit_{comp_id}"):
        ok, msg = submit_comp_entry(comp_id, username, athlete_name, picked, manual_pbs)
        if ok:
            st.success("報名已提交")
            st.rerun()
        st.warning(msg)
    if comp.get("is_registered") and c2.button("取消報名", key=f"student_comp_cancel_{comp_id}"):
        delete_comp_entry(comp_id, athlete_name)
        st.success("已取消報名")
        st.rerun()

    if comp.get("is_registered") and comp.get("my_events"):
        st.markdown("**已提交報名摘要**")
        for event in comp["my_events"]:
            pb = resolve_event_pb(athlete_name, event, comp.get("my_event_pbs"))
            st.write(
                f"• {event} — {pb.get('score') or '—'} "
                f"（{pb.get('comp_name') or '—'} · {pb.get('date') or '—'}）"
            )

    st.markdown("---")
    render_successful_registration_roster(comp_id)


def render_student_comp_registration(user: dict) -> None:
    ensure_youth_age_group_v_registrations()
    st.markdown("#### 🏅 比賽報名")
    st.caption("選擇參賽項目；如已有申報成績紀錄會自動帶入，否則請填寫該項目最佳成績。詳細個人資料請至「個人資料」分頁。")

    if not _profile_complete(user):
        st.warning("基本資料尚未完整，請先到「個人資料」填寫。")

    st.markdown("---")
    comps = get_student_competitions(user["name"])
    if not comps:
        st.info("教練尚未發布任何比賽。")
        return

    today = date.today().isoformat()
    upcoming = [c for c in comps if safe_str(c.get("date")) >= today]
    past = [c for c in comps if safe_str(c.get("date")) < today]

    if upcoming:
        st.markdown("##### 可報名比賽")
        for comp in upcoming:
            title = comp["name"]
            if comp.get("is_registered"):
                title += " ✅ 已報名"
            with st.expander(title, expanded=comp.get("is_registered", False)):
                _render_comp_signup(user, comp)

    if past:
        st.markdown("##### 過往比賽")
        for comp in reversed(past):
            events_text = "、".join(comp.get("my_events") or []) or "未報名"
            st.write(f"**{comp['name']}** ({comp['date']}) — {events_text}")
