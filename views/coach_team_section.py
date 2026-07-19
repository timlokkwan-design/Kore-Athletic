"""Coach team management — tabbed layout."""
from __future__ import annotations

import streamlit as st

from utils.config import EVENTS
from utils.data_store import (
    add_race_record,
    approve_pending_record,
    approve_specialty_change,
    approve_student,
    get_pending_users,
    get_student_names,
    get_students,
    load_pending_records,
    load_pending_specialty,
    load_race_records,
    load_users,
    remove_student,
    reject_specialty_change,
    reset_student_password,
)
from utils.helpers import format_birth_display, needs_wind, safe_str
from views.components.avatar import athlete_card_html, render_person


def _athlete_select(label: str, athletes: list[str], key: str) -> str | None:
    if not athletes:
        st.caption("尚無已核准學員")
        return None
    return st.selectbox(label, athletes, key=key)


def _render_pending_specialty() -> None:
    st.markdown("##### 待審批專項更改")
    pending_spec = load_pending_specialty()
    if pending_spec.empty:
        st.caption("無待審專項更改")
        return
    for _, p in pending_spec.iterrows():
        reason = safe_str(p.get("reason")) or "—"
        b1, b2, b3 = st.columns([4, 1, 1])
        b1.markdown(
            athlete_card_html(
                safe_str(p["name"]),
                f"{p['current_specialty']} → <b>{p['requested_specialty']}</b> "
                f"（{safe_str(p.get('date'))}）<br>原因：{reason}",
                username=safe_str(p.get("username")),
                bg="#fffbeb",
                border="#fcd34d",
                size=40,
            ),
            unsafe_allow_html=True,
        )
        if b2.button("核准", key=f"spec_ok_{p['id']}"):
            approve_specialty_change(str(p["id"]))
            st.rerun()
        if b3.button("拒絕", key=f"spec_no_{p['id']}"):
            reject_specialty_change(str(p["id"]))
            st.rerun()


def _render_pending_registrations() -> None:
    st.markdown("##### 待審批學員註冊")
    flash = st.session_state.pop("wa_notify_flash", None)
    if flash:
        st.success(f"✅ 已核准 **{flash.get('name', '')}**（{flash.get('username', '')}）")
        if flash.get("url"):
            st.link_button(
                "📱 WhatsApp 通知學員（一鍵發送）",
                flash["url"],
                use_container_width=True,
                type="primary",
            )
            st.caption("按鈕會開啟 WhatsApp 並帶好核准訊息（傳送至**學員**電話，不公開你的號碼）。")
        else:
            st.warning("學員未填電話，請以其他方式通知。")

    pending = get_pending_users()
    if pending.empty:
        st.caption("無待審學員")
        return
    for _, u in pending.iterrows():
        b1, b2 = st.columns([3, 1])
        b1.markdown(
            athlete_card_html(
                safe_str(u["name"]),
                f"{safe_str(u.get('name_en'))} · {safe_str(u.get('specialty'))} · "
                f"出生 {format_birth_display(u.to_dict())} · {safe_str(u.get('phone'))}",
                username=safe_str(u.get("username")),
                bg="#f8fafc",
                size=40,
            ),
            unsafe_allow_html=True,
        )
        if b2.button("核准", key=f"appr_{u['username']}"):
            from utils.whatsapp_notify import build_approval_notify

            approved = approve_student(u["username"])
            if approved:
                st.session_state["wa_notify_flash"] = build_approval_notify(approved)
            st.rerun()


def _render_pending_scores() -> None:
    st.markdown("##### 待審核比賽成績")
    pending_r = load_pending_records()
    if pending_r.empty:
        st.caption("無待審成績")
        return
    for _, p in pending_r.iterrows():
        b1, b2 = st.columns([3, 1])
        with b1:
            render_person(
                str(p["athlete_name"]),
                subtitle=(
                    f"{p['item']} ({p['score']}) · "
                    f"{safe_str(p.get('date'))} · {safe_str(p.get('comp_name'))}"
                ),
                size=36,
            )
        if b2.button("核准", key=f"pr_{p['id']}"):
            approve_pending_record(str(p["id"]))
            st.rerun()


def _render_active_roster() -> None:
    active = get_students()
    if not active:
        st.info("尚無已核准學員")
        return
    for u in active:
        render_person(
            safe_str(u["name"]),
            subtitle=safe_str(u.get("specialty")),
            username=safe_str(u.get("username")),
            size=36,
        )
    st.markdown("---")
    st.caption("移出隊伍後學員無法登入，訓練紀錄仍會保留。")
    pick = st.selectbox(
        "選擇要移除的學員",
        active,
        format_func=lambda u: f"{safe_str(u['name'])} ({safe_str(u['username'])})",
        key="team_remove_pick",
    )
    if st.button("移除學員", key="team_remove_btn", type="secondary"):
        st.session_state["team_remove_target"] = safe_str(pick["username"])
    if st.session_state.get("team_remove_target") == safe_str(pick["username"]):
        st.warning(f"確認將 **{safe_str(pick['name'])}** 移出隊伍？")
        y, n = st.columns(2)
        if y.button("確認移除", key="team_remove_confirm", type="primary"):
            remove_student(safe_str(pick["username"]))
            st.session_state.pop("team_remove_target", None)
            st.success(f"已移除 {safe_str(pick['name'])}")
            st.rerun()
        if n.button("取消", key="team_remove_cancel"):
            st.session_state.pop("team_remove_target", None)
            st.rerun()


def _render_password_reset() -> None:
    st.caption("學生忘記密碼時，請口頭或電話核對身分後重設，並將新密碼告知學生。")
    active = get_students()
    if not active:
        st.info("尚無學員")
        return
    reset_pick = st.selectbox(
        "選擇學員",
        active,
        format_func=lambda u: f"{safe_str(u['name'])} ({safe_str(u['username'])})",
        key="team_reset_pick",
    )
    new_pass = st.text_input("新密碼", type="password", key="team_reset_pass")
    confirm_pass = st.text_input("確認新密碼", type="password", key="team_reset_pass2")
    if st.button("重設密碼", type="primary", key="team_reset_btn"):
        if not new_pass:
            st.error("請輸入新密碼")
        elif new_pass != confirm_pass:
            st.error("兩次輸入的密碼不一致")
        else:
            ok, msg = reset_student_password(safe_str(reset_pick["username"]), new_pass)
            if ok:
                st.success(f"已重設 **{safe_str(reset_pick['name'])}** 的密碼，請通知學生使用新密碼登入。")
            else:
                st.error(msg)


def _render_contact_table() -> None:
    students = load_users()
    students = students[students["role"] == "student"] if not students.empty else students
    if students.empty:
        st.info("尚無學員資料")
        return
    display = students.copy()
    display["birth_display"] = display.apply(
        lambda row: format_birth_display(row.to_dict()),
        axis=1,
    )
    st.dataframe(
        display[
            [
                "name", "name_en", "birth_display", "gender", "hkaaa_id",
                "hk_permanent_resident", "specialty", "phone",
            ]
        ].rename(
            columns={
                "name": "中文名",
                "name_en": "英文名",
                "birth_display": "出生年月日",
                "gender": "性別",
                "hkaaa_id": "田總証編號",
                "hk_permanent_resident": "香港永久性居民",
                "specialty": "專項",
                "phone": "電話",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_score_management() -> None:
    st.markdown("##### 登錄官方成績")
    athletes = get_student_names()
    ra = _athlete_select("選手", athletes, key="race_a")
    ri = st.selectbox("項目", EVENTS, key="race_i")
    rd = st.date_input("日期", key="race_d")
    rs = st.text_input("成績", key="race_score")
    rc = st.text_input("比賽名稱", key="race_comp")
    if needs_wind(ri):
        rw = st.number_input("風速 m/s", step=0.1, key="race_w")
    else:
        rw = 0.0
        st.caption("此項目無需填寫風速")
    if ra and st.button("登錄成績", type="primary", key="race_save"):
        add_race_record({
            "athlete_name": ra,
            "item": ri,
            "score": rs,
            "date": rd.isoformat(),
            "wind": rw,
            "comp_name": rc,
        })
        st.success("已登錄")
        st.rerun()

    st.markdown("##### 大會歷史成績")
    races = load_race_records()
    if races.empty:
        st.caption("尚無紀錄")
        return
    st.dataframe(
        races.rename(
            columns={
                "athlete_name": "選手",
                "item": "項目",
                "score": "成績",
                "wind": "風速",
                "grade": "等級",
                "comp_name": "比賽",
                "date": "日期",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_coach_team() -> None:
    st.subheader("隊伍管理")
    team_tabs = ["待審事項", "活躍隊伍", "重設密碼", "成績管理", "聯絡總表"]
    if "coach_team_tab" not in st.session_state:
        st.session_state.coach_team_tab = team_tabs[0]

    tab = st.radio(
        "隊伍管理分頁",
        team_tabs,
        horizontal=True,
        key="coach_team_tab",
        label_visibility="collapsed",
    )

    if tab == "待審事項":
        _render_pending_specialty()
        st.divider()
        _render_pending_registrations()
        st.divider()
        _render_pending_scores()
    elif tab == "活躍隊伍":
        _render_active_roster()
    elif tab == "重設密碼":
        _render_password_reset()
    elif tab == "成績管理":
        _render_score_management()
    elif tab == "聯絡總表":
        _render_contact_table()
