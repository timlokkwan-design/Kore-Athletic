"""All V6 coach sub-sections."""

from datetime import date

import pandas as pd
import streamlit as st

from utils.acwr import acwr_status, calc_acwr, calc_load, estimate_workout_minutes, needs_rest
from utils.config import (
    CALENDAR_GROUP_FILTERS,
    EVENTS,
    GROUP_OPTIONS,
    SPECIALTY_OPTIONS,
    TAPER_DAYS,
    TECHNIQUE_LIB,
    VENUE_OPTIONS,
    WEEKDAY_OPTIONS,
    default_program,
    group_display_label,
    normalize_train_type,
)
from utils.data_store import (
    add_competition,
    add_injury,
    add_race_record,
    add_video,
    apply_recovery_template,
    apply_template,
    delete_template,
    approve_pending_record,
    approve_specialty_change,
    approve_student,
    attendance_rate,
    copy_program_to_dates,
    delete_program,
    delete_programs,
    days_until_competition,
    ensure_program_dict,
    build_coach_prog_map,
    filter_logs,
    filter_programs_by_group,
    get_all_logs,
    get_attendance_today,
    get_pending_users,
    get_program,
    get_programs_for_date,
    get_programs_for_month,
    get_student_names,
    get_students,
    get_wellness,
    load_attendance,
    load_competitions,
    load_injuries,
    parse_comp_events,
    load_pending_records,
    load_pending_specialty,
    load_periodization,
    load_programs,
    load_race_records,
    load_templates,
    load_users,
    load_videos,
    log_completion_rate,
    mark_leave,
    program_exists,
    purge_test_student_records,
    TEST_STUDENT_NAMES,
    remove_student,
    reject_specialty_change,
    reset_student_password,
    save_as_template,
    save_attendance,
    save_periodization,
    save_program,
    save_program_time_venue,
)
from utils.helpers import (
    day_sync_status,
    format_time_venue_line,
    format_timetable_date,
    normalize_date_str,
    program_specs,
    safe_float,
    safe_int,
    safe_str,
    needs_wind,
    short_group_label,
    parse_workout_volume,
    sync_status_label,
    workout_detail,
    weekly_summary_text,
    whatsapp_program_text,
)
from utils.coach_calendar_state import (
    get_coach_calendar_year_month,
    set_coach_calendar_date,
)
from views.components.coach_mobile_ui import render_coach_screen_switcher
from views.components.coach_program_editor import render_coach_day_editor
from views.components.calendar import render_calendar
from views.components.coach_sync import render_month_sync_alerts
from views.components.avatar import athlete_card_html, render_person


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


def _athlete_select(label: str, athletes: list[str], key: str) -> str | None:
    if not athletes:
        st.caption("尚無已核准學員")
        return None
    return st.selectbox(label, athletes, key=key)


def _clear_delete_targets() -> None:
    st.session_state.delete_target_dates = []


def _clear_copy_targets() -> None:
    st.session_state.copy_target_dates = []


@st.fragment
def _coach_calendar_pick_ui(copy_mode: bool, delete_mode: bool) -> None:
    """Fast multi-select: only reruns this block, not the program edit form."""
    flash = st.session_state.pop("copy_flash", None) or st.session_state.pop("sched_flash", None)
    if flash:
        kind, msg = flash
        (st.success if kind == "success" else st.error)(msg)

    from views.components.calendar import _render_calendar_impl

    _render_calendar_impl("coach_cal", show_acwr=False, copy_mode=copy_mode, delete_mode=delete_mode)

    from views.components.coach_mobile_ui import inject_coach_mobile_css, mark_force_row

    inject_coach_mobile_css()
    if delete_mode:
        targets = st.session_state.get("delete_target_dates", [])
        with st.container():
            mark_force_row()
            c1, c2, c3 = st.columns(3, gap="small")
            with c1:
                if st.button(
                    f"🗑 刪除 {len(targets)}",
                    key="prog_delete_confirm",
                    type="primary",
                    disabled=len(targets) == 0,
                    use_container_width=True,
                ):
                    n = delete_programs(targets)
                    st.session_state.delete_mode = False
                    st.session_state.pop("delete_target_dates", None)
                    st.session_state["sched_flash"] = ("success", f"已刪除 {n} 個日期的課表")
                    st.rerun()
            with c2:
                st.button(
                    "↺ 清除",
                    key="prog_delete_clear",
                    disabled=len(targets) == 0,
                    use_container_width=True,
                    on_click=_clear_delete_targets,
                )
            with c3:
                if st.button("✖ 取消", key="prog_delete_cancel", use_container_width=True):
                    st.session_state.delete_mode = False
                    st.session_state.pop("delete_target_dates", None)
                    st.rerun()
    elif copy_mode:
        targets = st.session_state.get("copy_target_dates", [])
        with st.container():
            mark_force_row()
            c1, c2, c3 = st.columns(3, gap="small")
            with c1:
                if st.button(
                    f"✅ 複製 {len(targets)}",
                    key="prog_copy_confirm",
                    type="primary",
                    disabled=len(targets) == 0,
                    use_container_width=True,
                ):
                    payload = st.session_state.get("copy_source_payload")
                    src = st.session_state.get("copy_source_date", "")
                    n = copy_program_to_dates(src, targets, payload)
                    st.session_state.copy_mode = False
                    st.session_state.pop("copy_source_date", None)
                    st.session_state.pop("copy_source_payload", None)
                    st.session_state.pop("copy_target_dates", None)
                    if n and targets:
                        set_coach_calendar_date(targets[-1])
                    st.session_state["copy_flash"] = (
                        "success",
                        f"已複製至 {n} 個日期：{', '.join(targets)}",
                    )
                    st.rerun()
            with c2:
                st.button(
                    "↺ 清除",
                    key="prog_copy_clear",
                    disabled=len(targets) == 0,
                    use_container_width=True,
                    on_click=_clear_copy_targets,
                )
            with c3:
                if st.button("✖ 取消", key="prog_copy_cancel", use_container_width=True):
                    st.session_state.copy_mode = False
                    st.session_state.pop("copy_source_date", None)
                    st.session_state.pop("copy_source_payload", None)
                    st.session_state.pop("copy_target_dates", None)
                    st.rerun()


def render_coach_program() -> None:
    st.subheader("📅 月曆訓練計畫與 ACWR")
    per = load_periodization()
    try:
        comp_date = date.fromisoformat(str(per["comp_target_date"]))
    except ValueError:
        comp_date = date.today()

    countdown = days_until_competition()
    m1, m2 = st.columns([1, 2])
    m1.metric("校際賽倒數", f"{countdown} 天" if countdown is not None else "—")
    with m2:
        with st.expander("⚙️ 賽事倒數設定", expanded=False):
            cd = st.date_input("校際賽倒數目標日", value=comp_date, key="prog_comp_date")
            if st.button("儲存賽事倒數", key="prog_save_period"):
                save_periodization({
                    "global_phase": per.get("global_phase", ""),
                    "global_week_theme": per.get("global_week_theme", ""),
                    "comp_target_date": cd.isoformat(),
                })
                st.success("已儲存賽事倒數")
                st.rerun()

    copy_mode = st.session_state.get("copy_mode", False)
    delete_mode = st.session_state.get("delete_mode", False)
    flash = st.session_state.pop("copy_flash", None) or st.session_state.pop("sched_flash", None)
    prog_flash = st.session_state.pop("prog_save_flash", None)
    if flash:
        kind, msg = flash
        (st.success if kind == "success" else st.error)(msg)
    if prog_flash:
        st.success(prog_flash)

    if not copy_mode and not delete_mode:
        st.caption(
            "只顯示訓練時間表已排程的日子 · 日曆預設 · 點選日期直接編輯跑案"
        )

    if copy_mode or delete_mode:
        _coach_calendar_pick_ui(copy_mode, delete_mode)
        return

    _render_coach_program_editor()


def _render_coach_log_filter() -> None:
    test_logs = get_all_logs()
    test_count = int(test_logs["student_name"].astype(str).isin(TEST_STUDENT_NAMES).sum()) if not test_logs.empty else 0
    if test_count:
        if st.button(f"🧹 清除測試學員日誌（{test_count} 筆：陳大文、林明美等）", key="purge_test_logs"):
            stats = purge_test_student_records(clear_programs=False)
            st.success(f"已清除 {stats.get('logs_removed', 0)} 筆測試日誌")
            st.rerun()
    f1, f2, f3 = st.columns(3)
    fd = f1.date_input("日期", value=None, key="log_filter_date")
    athletes = [n for n in get_student_names() if n not in TEST_STUDENT_NAMES]
    fs = f2.selectbox("學員", [""] + athletes, key="log_filter_student")
    fr = f3.selectbox("RPE", ["", "1-4", "5-7", "8-10"], key="log_filter_rpe")
    logs = filter_logs(
        fd.isoformat() if fd else None,
        fr or None,
        fs or None,
        exclude_test=True,
    )
    for _, log in logs.head(30).iterrows():
        remark = safe_str(log.get("laps_text")) or safe_str(log.get("remark"))
        render_person(
            str(log["student_name"]),
            subtitle=f"`{log['date']}` — {remark} · RPE{log['rpe']} · Load{log.get('load', '')}",
            size=32,
        )


def _render_calendar_group_filter() -> tuple[str, str | None]:
    """Compact one-row group filter for calendar view only (not the editor)."""
    from views.components.coach_mobile_ui import force_button_row

    # Editor no longer switches groups — calendar filter stays simple.
    filters = [
        ("全部組別", None),
        ("短跑", "短跑組"),
        ("中長跑", "中長跑組"),
        ("其他", "跨欄組"),
    ]
    labels = [label for label, _ in filters]
    values = [value for _, value in filters]
    chip = {
        "全部組別": "全部",
        "短跑": "短跑",
        "中長跑": "中長跑",
        "其他": "其他",
    }
    key = "coach_cal_group_filter_idx"
    if key not in st.session_state:
        # Migrate legacy selectbox label if present
        legacy = st.session_state.get("coach_cal_group_filter")
        if legacy in labels:
            st.session_state[key] = labels.index(legacy)
        else:
            st.session_state[key] = 0
    cur = int(st.session_state[key])
    if cur < 0 or cur >= len(labels):
        cur = 0
        st.session_state[key] = 0

    st.caption("選擇組別")
    with force_button_row(key="coach_cal_grp_row", n_cols=len(labels)) as cols:
        for i, (col, label) in enumerate(zip(cols, labels)):
            with col:
                if st.button(
                    chip.get(label, label),
                    key=f"coach_cal_grp_{i}",
                    use_container_width=True,
                    type="primary" if i == cur else "secondary",
                ):
                    st.session_state[key] = i
                    st.rerun()
    return labels[cur], values[cur]


def _render_coach_program_editor() -> None:
    from views.components.coach_mobile_ui import inject_coach_mobile_css, mark_force_row

    inject_coach_mobile_css()
    screen = st.session_state.get("coach_prog_screen", "cal")
    render_coach_screen_switcher(current=screen)

    # Group filter only on calendar screen — keeps edit view clean and
    # avoids filter CSS interacting with day-editor controls.
    cal_group_label, cal_group = "全部組別", None
    if screen == "cal":
        cal_group_label, cal_group = _render_calendar_group_filter()

    cal_year, cal_month = get_coach_calendar_year_month()
    alert_map = build_coach_prog_map(
        filter_programs_by_group(get_programs_for_month(cal_year, cal_month), cal_group)
    )

    if screen == "cal":
        render_month_sync_alerts(alert_map, page="prog")
        selected = render_calendar(
            "coach_cal",
            show_acwr=True,
            copy_mode=False,
            delete_mode=False,
            group_filter=cal_group,
            goto_edit_on_select=True,
            schedule_only=True,
        )
        with st.container():
            mark_force_row()
            b_copy, b_delete = st.columns(2, gap="small")
            with b_copy:
                if st.button("📋 複製課表", key="prog_copy_btn", use_container_width=True):
                    src = st.session_state.get("coach_cal", selected.isoformat())
                    st.session_state.copy_mode = True
                    st.session_state.delete_mode = False
                    st.session_state.copy_source_date = src
                    st.session_state.copy_source_payload = get_programs_for_date(selected)
                    st.session_state.copy_target_dates = []
                    st.rerun()
            with b_delete:
                if st.button("🗑 多選刪除", key="prog_delete_btn", use_container_width=True):
                    st.session_state.delete_mode = True
                    st.session_state.copy_mode = False
                    st.session_state.delete_target_dates = []
                    st.rerun()
        st.caption(f"今日完成率：**{log_completion_rate()}%**")
        if st.button("📍 今日課表", use_container_width=True, key="coach_goto_today"):
            set_coach_calendar_date(date.today().isoformat())
            st.session_state.coach_prog_screen = "edit"
            st.rerun()
    else:
        sk = st.session_state.get("coach_cal", date.today().isoformat())
        try:
            edit_date = date.fromisoformat(str(sk))
        except ValueError:
            edit_date = date.today()
        st.caption(f"編輯 **{format_timetable_date(sk)}** · 組別篩選：{cal_group_label}")
        if st.button("← 返回日曆", use_container_width=True, key="coach_back_cal"):
            st.session_state.coach_prog_screen = "cal"
            st.rerun()
        render_coach_day_editor(edit_date)

    with st.expander("📊 訓練日誌篩選", expanded=False):
        _render_coach_log_filter()


def render_coach_wellness() -> None:
    st.subheader("❤️ 團隊 ACWR 與健康預警")
    logs, students = get_all_logs(), get_students()
    athletes = [safe_str(s.get("name")) for s in students]
    if not athletes:
        st.info("尚無已核准學員，請先在「隊伍管理」核准註冊。")
    else:
        cols = st.columns(min(max(len(students), 1), 3))
        for i, student in enumerate(students):
            name = safe_str(student.get("name"))
            username = safe_str(student.get("username"))
            acwr = calc_acwr(logs, name)
            w = get_wellness(athlete=name)
            label, color = acwr_status(acwr)
            rest = needs_rest(acwr, w)
            inj = load_injuries()
            restricted = (
                not inj[
                    (inj["athlete_name"] == name)
                    & (inj["restrict"].astype(str).isin(["True", "true", "1"]))
                ].empty
                if not inj.empty
                else False
            )
            bg = "#fee2e2" if rest or restricted else "#dcfce7"
            body = (
                f"ACWR {label}<br>"
                f"<small>睡眠:{w['sleep'] if w else '-'} "
                f"酸痛:{w['soreness'] if w else '-'} "
                f"心情:{w['mood'] if w else '-'}"
                f"{' 🤒' if w and w.get('sick') else ''}</small>"
                f"{'<br><b style=\"color:red\">⚠️ 建議休息/減量</b>' if rest else ''}"
            )
            with cols[i % len(cols)]:
                st.markdown(
                    athlete_card_html(name, body, username=username, bg=bg),
                    unsafe_allow_html=True,
                )

    st.subheader("🤕 傷患追蹤")
    c1, c2 = st.columns(2)
    with c1:
        athlete = _athlete_select("選手", athletes, key="inj_ath")
        body = st.text_input("受傷部位", key="inj_body")
        inj_date = st.date_input("日期", key="inj_d")
        diag = st.text_input("診斷", key="inj_diag")
        rehab = st.text_area("復康計劃", key="inj_rehab")
        restrict = st.checkbox("限制高強度訓練", key="inj_restrict")
        alt = st.text_input("替代訓練", "游泳/核心/上肢訓練", key="inj_alt")
        if athlete and st.button("記錄傷患", type="primary", key="inj_save"):
            add_injury({
                "athlete_name": athlete,
                "body_part": body,
                "date": inj_date.isoformat(),
                "diagnosis": diag,
                "rehab": rehab,
                "restrict": restrict,
                "alt_training": alt,
            })
            st.success("已記錄")
            st.rerun()
    with c2:
        inj_df = load_injuries()
        if inj_df.empty:
            st.write("無傷患紀錄")
        else:
            for _, row in inj_df.iterrows():
                render_person(
                    str(row["athlete_name"]),
                    subtitle=f"{row['body_part']} ({row['date']}) — {row['diagnosis']}"
                    + (
                        " ⚠️ 限制訓練"
                        if str(row.get("restrict")) in ("True", "true", "1")
                        else ""
                    ),
                    size=36,
                )

    st.subheader("✅ 今日出席快覽")
    st.caption("完整月曆出席表請見「出席表」分頁。")
    c1, c2 = st.columns(2)
    with c1:
        for student in students:
            name = safe_str(student.get("name"))
            att = get_attendance_today()
            row = att[att["athlete_name"] == name] if not att.empty else pd.DataFrame()
            if row.empty:
                subtitle = "❌ 缺席"
            elif row.iloc[0]["status"] == "present":
                subtitle = f"✅ 出席 {row.iloc[0]['detail']}"
            else:
                subtitle = f"📝 請假 {row.iloc[0]['detail']}"
            render_person(name, subtitle=subtitle, username=safe_str(student.get("username")), size=32)
    with c2:
        st.markdown("**出席率統計**")
        for student in students:
            name = safe_str(student.get("name"))
            render_person(
                name,
                subtitle=f"**{attendance_rate(name)}%**",
                username=safe_str(student.get("username")),
                size=32,
            )


def render_coach_team() -> None:
    from views.coach_team_section import render_coach_team as _render

    _render()


def render_coach_comp() -> None:
    st.subheader("🏅 測試/比賽日曆")
    c1, c2 = st.columns(2)
    with c1:
        cn = st.text_input("比賽名稱", key="comp_name")
        cd = st.date_input("比賽日期", key="comp_d")
        ce = st.selectbox("項目", EVENTS, key="comp_e")
        cl = st.text_input("地點", key="comp_loc")
        if st.button("新增比賽", type="primary", key="comp_add"):
            add_competition({"name": cn, "date": cd.isoformat(), "event": ce, "location": cl})
            st.success("已新增")
            st.rerun()
    with c2:
        comps = load_competitions()
        if comps.empty:
            st.write("無比賽")
        else:
            for _, c in comps.iterrows():
                events = parse_comp_events(c.get("event"))
                event_text = "、".join(events) if events else safe_str(c.get("event"))
                st.markdown(
                    f"**{c['name']}** {c['date']} — {event_text} @ {c['location']}"
                )
            st.caption("報名名單及詳細資料請在「比賽報名表」分頁設定。")

    st.markdown("#### 📉 減量建議 (依項目距離)")
    st.write(" · ".join(f"{ev}: 賽前 {d} 天減量" for ev, d in TAPER_DAYS.items()))

    st.markdown("#### 🔄 賽後恢復範本")
    st.write(
        "Day 1-2: 恢復跑 20-30min RPE 3-4 | Day 3: 技術課輕量 | "
        "Day 4-5: 漸進恢復 | Day 6+: 依 ACWR 恢復正常"
    )
    rec_start = st.date_input("套用起始日期", value=date.today(), key="rec_start")
    if st.button("套用至選定日期後", key="rec_apply"):
        apply_recovery_template(rec_start)
        st.success("已套用賽後恢復範本")
        st.rerun()


def render_coach_video() -> None:
    st.subheader("🎬 影片分析")
    c1, c2 = st.columns(2)
    athletes = get_student_names()
    with c1:
        va = _athlete_select("選手", athletes, key="vid_a")
        vurl = st.text_input("YouTube / Drive 連結", key="vid_url")
        vts = st.text_input("時間戳", placeholder="0:12 起跑", key="vid_ts")
        vnotes = st.text_area("教練評語", key="vid_notes")
        vissue = st.selectbox(
            "技術問題",
            [t["issue"] for t in TECHNIQUE_LIB],
            key="vid_issue",
        )
        if va and st.button("儲存分析", type="primary", key="vid_save"):
            add_video({
                "athlete_name": va,
                "url": vurl,
                "timestamp": vts,
                "notes": vnotes,
                "issue": vissue,
            })
            st.success("已儲存")
            st.rerun()
    with c2:
        st.markdown("#### 技術問題庫")
        for t in TECHNIQUE_LIB:
            st.markdown(f"**{t['issue']}** → {t['fix']}")

    videos = load_videos()
    if not videos.empty:
        for _, v in videos.iterrows():
            render_person(str(v["athlete_name"]), size=36)
            st.markdown(
                f"[{v['url']}]({v['url']}) · ⏱ {v['timestamp']} · 問題: {v['issue']}\n*{v['notes']}*"
            )


def render_coach_comm() -> None:
    st.subheader("💬 每週訓練摘要 (家長溝通)")
    athletes = get_student_names()
    athlete = _athlete_select("選擇學員", athletes, key="comm_athlete")
    if athlete and st.button("生成摘要", type="primary", key="comm_gen"):
        logs = get_all_logs()
        att = load_attendance()
        att_sub = att[att["athlete_name"] == athlete] if not att.empty else att
        pbs = load_race_records()
        pbs_sub = pbs[pbs["athlete_name"] == athlete] if not pbs.empty else pbs
        text = weekly_summary_text(
            athlete,
            logs[logs["student_name"] == athlete],
            att_sub,
            pbs_sub,
            calc_acwr(logs, athlete),
            load_periodization(),
        )
        st.session_state.summary_text = text
    if st.session_state.get("summary_text"):
        st.text_area("摘要", st.session_state.summary_text, height=300, key="comm_summary")
        st.code(st.session_state.summary_text)


# Re-export for backwards compatibility
from views.coach_schedule_section import render_coach_schedule  # noqa: E402, F401
