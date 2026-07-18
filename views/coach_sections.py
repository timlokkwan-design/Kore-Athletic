"""All V6 coach sub-sections."""

from datetime import date

import pandas as pd
import streamlit as st

from utils.acwr import acwr_status, calc_acwr, calc_load, needs_rest
from utils.config import (
    EVENTS,
    GROUP_OPTIONS,
    PHASE_OPTIONS,
    SPECIALTY_OPTIONS,
    TAPER_DAYS,
    TECHNIQUE_LIB,
    TRAIN_TYPE_OPTIONS,
    VENUE_OPTIONS,
    WEEKDAY_OPTIONS,
    WEEK_THEME_OPTIONS,
    normalize_train_type,
)
from utils.data_store import (
    add_competition,
    add_injury,
    add_race_record,
    add_video,
    apply_recovery_template,
    apply_template,
    approve_pending_record,
    approve_specialty_change,
    approve_student,
    attendance_rate,
    copy_program_to_dates,
    delete_program,
    delete_programs,
    days_until_competition,
    ensure_program_dict,
    filter_logs,
    get_all_logs,
    get_attendance_today,
    get_pending_users,
    get_program,
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
    format_timetable_date,
    normalize_date_str,
    program_specs,
    safe_float,
    safe_int,
    safe_str,
    needs_wind,
    weekly_summary_text,
    whatsapp_program_text,
)
from views.components.calendar import render_calendar
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

    if delete_mode:
        targets = st.session_state.get("delete_target_dates", [])
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(
                f"🗑 確認刪除 {len(targets)} 個課表",
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
                "↺ 清除已選",
                key="prog_delete_clear",
                disabled=len(targets) == 0,
                use_container_width=True,
                on_click=_clear_delete_targets,
            )
        with c3:
            if st.button("✖ 取消刪除", key="prog_delete_cancel", use_container_width=True):
                st.session_state.delete_mode = False
                st.session_state.pop("delete_target_dates", None)
                st.rerun()
    elif copy_mode:
        targets = st.session_state.get("copy_target_dates", [])
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(
                f"✅ 確認複製到 {len(targets)} 個日期",
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
                    st.session_state["coach_cal"] = targets[-1]
                    st.session_state.cal_year = date.fromisoformat(targets[-1]).year
                    st.session_state.cal_month = date.fromisoformat(targets[-1]).month
                st.session_state["copy_flash"] = (
                    "success",
                    f"已複製至 {n} 個日期：{', '.join(targets)}",
                )
                st.rerun()
        with c2:
            st.button(
                "↺ 清除已選",
                key="prog_copy_clear",
                disabled=len(targets) == 0,
                use_container_width=True,
                on_click=_clear_copy_targets,
            )
        with c3:
            if st.button("✖ 取消複製", key="prog_copy_cancel", use_container_width=True):
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
    c1, c2, c3 = st.columns(3)
    with c1:
        gp = st.selectbox(
            "全局訓練階段",
            PHASE_OPTIONS,
            index=_select_index(PHASE_OPTIONS, per["global_phase"]),
            key="prog_global_phase",
        )
    with c2:
        gw = st.selectbox(
            "本週主題",
            WEEK_THEME_OPTIONS,
            index=_select_index(WEEK_THEME_OPTIONS, per["global_week_theme"]),
            key="prog_global_week",
        )
    with c3:
        cd = st.date_input("校際賽倒數目標日", value=comp_date, key="prog_comp_date")
    if st.button("儲存週期化設定", key="prog_save_period"):
        save_periodization({
            "global_phase": gp,
            "global_week_theme": gw,
            "comp_target_date": cd.isoformat(),
        })
        st.success("已儲存")
        st.rerun()

    copy_mode = st.session_state.get("copy_mode", False)
    delete_mode = st.session_state.get("delete_mode", False)
    flash = st.session_state.pop("copy_flash", None) or st.session_state.pop("sched_flash", None)
    if flash:
        kind, msg = flash
        (st.success if kind == "success" else st.error)(msg)

    if not copy_mode and not delete_mode:
        st.caption(
            "💡 複製課表：先點選來源日期 → 按「複製課表到其他日期」→ "
            "在月曆**多選**目標日期 → 確認複製 · "
            "刪除課表：按「多選刪除課表」可一次刪除多個日期"
        )

    if copy_mode or delete_mode:
        _coach_calendar_pick_ui(copy_mode, delete_mode)
        return

    _render_coach_program_editor()


@st.fragment
def _render_coach_program_editor() -> None:
    selected = render_calendar("coach_cal", show_acwr=True, copy_mode=False, delete_mode=False)

    b_copy, b_delete = st.columns(2)
    with b_copy:
        if st.button("📋 複製課表到其他日期", key="prog_copy_btn", use_container_width=True):
            src = st.session_state.get("coach_cal", selected.isoformat())
            st.session_state.copy_mode = True
            st.session_state.delete_mode = False
            st.session_state.copy_source_date = src
            st.session_state.copy_source_payload = ensure_program_dict(get_program(selected))
            st.session_state.copy_target_dates = []
            st.rerun()
    with b_delete:
        if st.button("🗑 多選刪除課表", key="prog_delete_btn", use_container_width=True):
            st.session_state.delete_mode = True
            st.session_state.copy_mode = False
            st.session_state.delete_target_dates = []
            st.rerun()

    st.caption(f"今日完成率：**{log_completion_rate()}%**")

    st.markdown("#### 編輯當日訓練計劃")
    prog = ensure_program_dict(get_program(selected))
    sk = selected.isoformat()

    ptype_key = f"ptype_{sk}"
    default_type = normalize_train_type(prog["type"])
    if ptype_key not in st.session_state:
        st.session_state[ptype_key] = default_type
    elif st.session_state[ptype_key] not in TRAIN_TYPE_OPTIONS:
        st.session_state[ptype_key] = normalize_train_type(st.session_state[ptype_key])

    train_type = normalize_train_type(
        st.selectbox("訓練類型", TRAIN_TYPE_OPTIONS, key=ptype_key)
    )

    sets = safe_int(prog["sets"])
    reps = safe_int(prog["reps"])
    dist = safe_int(prog["dist"])
    rest = safe_str(prog.get("rest"))
    target_sec = safe_float(prog.get("target_seconds"))
    exercises = safe_str(prog.get("exercises"))
    tech_focus = safe_str(prog.get("tech_focus"))
    field_event = safe_str(prog.get("field_event"), "跳遠")
    attempts = safe_int(prog.get("attempts"), 10)
    phase = week_theme = tips = ""
    duration = 0
    rpe = 7

    if train_type == "比賽":
        st.info("🏁 比賽日 — 按「儲存課表」後，月曆將直接顯示「比賽」")
        title = "比賽"
        group = "全體組員"
        sets = reps = dist = attempts = 0
        rest = exercises = tech_focus = field_event = ""
        target_sec = 0.0
    else:
        title = st.text_input("訓練名稱", safe_str(prog["title"]), key=f"ptitle_{sk}")
        group = st.selectbox(
            "針對組別",
            GROUP_OPTIONS,
            index=_select_index(GROUP_OPTIONS, prog["group"], default=3),
            key=f"pgroup_{sk}",
        )

        if train_type in ("間歇跑", "節奏跑", "恢復跑"):
            r1, r2, r3, r4 = st.columns(4)
            sets = r1.number_input("組數", 0, 20, sets, key=f"psets_{sk}")
            reps = r2.number_input("趟數", 0, 30, reps, key=f"preps_{sk}")
            dist = r3.number_input("距離(m)", 0, 5000, dist, key=f"pdist_{sk}")
            target_sec = r4.number_input(
                "目標秒數", 0.0, 999.0, target_sec, step=0.1, key=f"ptarget_{sk}"
            )
            rest = st.text_input(
                "休息", rest or "組間休息 90 秒", key=f"prest_{sk}"
            )
        elif train_type == "肌力課":
            exercises = st.text_input(
                "動作項目",
                exercises,
                placeholder="深蹲、爆發起跳...",
                key=f"pexercises_{sk}",
            )
        elif train_type == "技術課":
            tech_focus = st.text_input("技術重點", tech_focus, key=f"ptech_{sk}")
        elif train_type == "休息":
            st.info("休息日 — 無訓練安排")

        default_duration = safe_int(prog.get("duration"), 0 if train_type == "休息" else 60)
        default_rpe = max(
            1, safe_int(prog.get("rpe"), 4 if train_type in ("恢復跑", "休息") else 7)
        )

        d1, d2, d3, d4 = st.columns(4)
        duration = d1.number_input("時長(分)", 0, 300, default_duration, key=f"pdur_{sk}")
        rpe = d2.number_input("預期 RPE", 1, 10, default_rpe, key=f"prpe_{sk}")
        phase = d3.selectbox(
            "本日階段",
            [""] + PHASE_OPTIONS,
            index=_select_index([""] + PHASE_OPTIONS, prog.get("phase")),
            key=f"pphase_{sk}",
        )
        week_theme = d4.selectbox(
            "本週主題",
            [""] + WEEK_THEME_OPTIONS,
            index=_select_index([""] + WEEK_THEME_OPTIONS, prog.get("week_theme")),
            key=f"pweek_{sk}",
        )
        tips = st.text_area("教練指導", safe_str(prog.get("tips")), key=f"ptips_{sk}")

    load = calc_load(train_type, duration, rpe, int(sets or 0), int(reps or 0), int(dist or 0))
    if train_type != "比賽":
        athletes = get_student_names()
        acwr_v, _ = acwr_status(
            calc_acwr(get_all_logs(), athletes[0] if athletes else "", selected)
        )
        st.markdown(f"**加權負荷：{load}** · **ACWR 預警：{acwr_v}**")

    b1, b2, b3 = st.columns(3)
    if b1.button("💾 儲存課表", type="primary", use_container_width=True, key=f"psave_{sk}"):
        save_program({
            "date": sk,
            "type": train_type,
            "title": title,
            "group": group,
            "sets": sets,
            "reps": reps,
            "dist": dist,
            "rest": rest,
            "duration": duration,
            "rpe": rpe,
            "tips": tips,
            "phase": phase,
            "week_theme": week_theme,
            "target_seconds": target_sec,
            "exercises": exercises,
            "tech_focus": tech_focus,
            "field_event": field_event,
            "attempts": attempts,
            "start_time": safe_str(prog.get("start_time")),
            "end_time": safe_str(prog.get("end_time")),
            "venue": safe_str(prog.get("venue")),
            "venue_other": safe_str(prog.get("venue_other")),
        })
        st.success("課表已儲存！")
        st.rerun()
    if b2.button("📁 存範本", use_container_width=True, key=f"ptpl_{sk}"):
        save_as_template({
            "type": train_type,
            "title": title,
            "group": group,
            "sets": sets,
            "reps": reps,
            "dist": dist,
            "rest": rest,
            "duration": duration,
            "rpe": rpe,
            "tips": tips,
            "phase": phase,
            "week_theme": week_theme,
            "target_seconds": target_sec,
            "exercises": exercises,
            "tech_focus": tech_focus,
            "field_event": field_event,
            "attempts": attempts,
        })
        st.success("已存範本")
    if b3.button("🗑 刪除當日課表", use_container_width=True, key=f"pdelete_{sk}"):
        if program_exists(selected):
            delete_program(selected)
            st.success(f"已刪除 {sk} 的課表")
            st.rerun()
        else:
            st.info("此日沒有已儲存的課表（月曆顯示為預設休息）")

    with st.expander("📱 WhatsApp 課表文案"):
        txt = whatsapp_program_text(
            {
                **prog,
                "date": sk,
                "title": title,
                "type": train_type,
                "group": group,
                "tips": tips,
            },
            load_periodization(),
        )
        st.code(txt, language=None)

    with st.expander("📚 課表範本庫"):
        templates = load_templates()
        if templates.empty:
            st.write("尚無範本")
        else:
            for _, t in templates.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"{t['title']} ({t['type']})")
                if c2.button("套用", key=f"tpl_{t['id']}"):
                    apply_template(str(t["id"]), sk)
                    st.rerun()

    st.markdown("#### 訓練日誌篩選")
    test_logs = filter_logs(exclude_test=False)
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
