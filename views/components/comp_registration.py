"""Student competition registration — pick events; manual PB only when no record."""
from __future__ import annotations

from datetime import date

import streamlit as st

from utils.data_store import (
    delete_comp_entry,
    ensure_youth_age_group_v_registrations,
    get_best_performance_last_year,
    get_student_competitions,
    is_registration_open,
    registration_status,
    registration_status_label,
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


def _render_comp_signup(user: dict, comp: dict, *, allow_submit: bool) -> None:
    comp_id = comp["id"]
    athlete_name = user["name"]
    username = user["username"]
    available = comp.get("events") or []
    status = registration_status(comp)

    date_label = format_timetable_date(comp["date"]) if comp.get("date") else "—"
    st.markdown(f"**{comp['name']}** · {date_label} · {comp.get('location') or '—'}")
    if comp.get("link"):
        st.markdown(f"🔗 [比賽連結]({comp['link']})")

    if status == "pending_deadline":
        st.warning("報名截止日期有待教練填寫，暫未能報名。")
    elif status == "closed":
        deadline = safe_str(comp.get("deadline"))
        st.error(f"已過報名截止日期（{deadline or '—'}），未能報名。")
    elif comp.get("deadline"):
        st.caption(f"報名截止：{comp['deadline']}")

    if comp.get("notes"):
        st.info(comp["notes"])

    if not available:
        st.warning("此比賽尚未開放項目。")
        render_successful_registration_roster(comp_id)
        return

    if allow_submit and is_registration_open(comp):
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
    elif comp.get("is_registered") and comp.get("my_events"):
        st.caption("報名已截止或暫未開放；以下為你已提交的報名。")

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
    st.caption(
        "選擇參賽項目；如已有申報成績紀錄會自動帶入，否則請填寫該項目最佳成績。"
        "過了報名截止日期後不能報名；下一個比賽須等教練填寫截止日期後才開放。"
    )

    if not _profile_complete(user):
        st.warning("基本資料尚未完整，請先到「個人資料」填寫。")

    st.markdown("---")
    comps = get_student_competitions(user["name"])
    if not comps:
        st.info("教練尚未發布任何比賽。")
        return

    today = date.today().isoformat()
    # 僅顯示已設定開放項目的比賽（純預告見「賽事時間表」）
    open_for_signup = [c for c in comps if c.get("events")]
    if not open_for_signup:
        st.info("暫無可報名比賽。賽事日期預告請見「賽事時間表」。")
        return

    open_now = [c for c in open_for_signup if registration_status(c, today=today) == "open"]
    pending = [c for c in open_for_signup if registration_status(c, today=today) == "pending_deadline"]
    closed = [c for c in open_for_signup if registration_status(c, today=today) == "closed"]
    # Sort soonest first
    open_now.sort(key=lambda c: (safe_str(c.get("date")), safe_str(c.get("name"))))
    pending.sort(key=lambda c: (safe_str(c.get("date")), safe_str(c.get("name"))))
    closed.sort(key=lambda c: (safe_str(c.get("date")), safe_str(c.get("name"))), reverse=True)

    # Roster overview
    st.markdown("##### ✅ 成功報名名單")
    for comp in open_for_signup:
        status = registration_status(comp, today=today)
        tag = registration_status_label(status)
        entries_title = f"{comp['name']} · {comp.get('date') or '—'} · {tag}"
        with st.expander(entries_title, expanded=False):
            render_successful_registration_roster(comp["id"])

    if open_now:
        st.markdown("##### 可報名比賽")
        for comp in open_now:
            title = comp["name"]
            if comp.get("deadline"):
                title += f" · 截止 {comp['deadline']}"
            if comp.get("is_registered"):
                title += " ✅ 已報名"
            with st.expander(title, expanded=True):
                _render_comp_signup(user, comp, allow_submit=True)
    else:
        st.info("目前沒有開放報名的比賽。")

    if pending:
        st.markdown("##### 下一個比賽（截止日期有待教練填寫）")
        st.caption("上一個報名截止後，教練填寫下一個比賽的截止日期，即可開放報名。")
        for i, comp in enumerate(pending):
            title = f"{comp['name']} · {comp.get('date') or '—'}"
            with st.expander(title, expanded=(i == 0 and not open_now)):
                _render_comp_signup(user, comp, allow_submit=False)

    if closed:
        st.markdown("##### 已截止報名")
        for comp in closed:
            title = f"{comp['name']} · 截止 {comp.get('deadline') or '—'}"
            if comp.get("is_registered"):
                title += " ✅ 已報名"
            with st.expander(title, expanded=False):
                _render_comp_signup(user, comp, allow_submit=False)
