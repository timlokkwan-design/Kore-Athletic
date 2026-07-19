"""Coach daily program editor — mobile-friendly layout."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from utils.acwr import acwr_status, calc_acwr, calc_load, estimate_workout_minutes
from utils.config import (
    GROUP_OPTIONS,
    default_program,
    group_display_label,
    normalize_group,
    normalize_train_type,
)
from utils.data_store import (
    apply_template,
    delete_program,
    delete_template,
    ensure_program_dict,
    get_all_logs,
    get_group_program_for_date,
    get_programs_for_date,
    get_student_names,
    load_periodization,
    load_templates,
    program_exists,
    save_as_template,
    save_program,
)
from utils.helpers import (
    day_sync_status,
    format_time_venue_line,
    format_timetable_date,
    parse_workout_volume,
    safe_int,
    safe_str,
    short_group_label,
    saved_workout_text,
    saved_coach_tips,
    sync_status_label,
    whatsapp_program_text,
)
from views.components.coach_workout_compare import render_workout_history_compare


def _apply_workout_copy(sk: str, edit_group: str, source: dict) -> None:
    """Fill editor widgets from a source program (after rerun)."""
    st.session_state[f"pworkout_{sk}_{edit_group}"] = saved_workout_text(source)
    st.session_state[f"ptips_{sk}_{edit_group}"] = saved_coach_tips(source)
    st.session_state[f"prpe_{sk}_{edit_group}"] = max(1, safe_int(source.get("rpe"), 7))
    st.session_state[f"pstatus_{sk}_{edit_group}"] = "訓練"


def _copy_last_week_same_day(sk: str, edit_group: str, selected: date) -> None:
    src_date = selected - timedelta(days=7)
    source = get_group_program_for_date(src_date, edit_group)
    if not source:
        st.session_state[f"pcopy_flash_{sk}_{edit_group}"] = (
            "warn",
            f"上週同天（{format_timetable_date(src_date.isoformat())}）尚無 {short_group_label(edit_group)} 課表",
        )
        return
    body = saved_workout_text(source)
    if not body:
        st.session_state[f"pcopy_flash_{sk}_{edit_group}"] = (
            "warn",
            f"上週同天（{format_timetable_date(src_date.isoformat())}）沒有跑案文字",
        )
        return
    _apply_workout_copy(sk, edit_group, source)
    st.session_state[f"pcopy_flash_{sk}_{edit_group}"] = (
        "success",
        f"已複製 {format_timetable_date(src_date.isoformat())} 的跑案，請確認後儲存",
    )


def inject_coach_editor_css() -> None:
    st.markdown(
        """
        <style>
        /* Keep coach editor button rows on one line (mobile otherwise stacks columns) */
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-grp-marker) > [data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-status-marker) > [data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-save-marker) > [data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-more-marker) > [data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-copy-marker) > [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.35rem !important;
            width: 100% !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-grp-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-status-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-save-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-more-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-copy-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 0 !important;
            flex: 1 1 0 !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-status-marker) > [data-testid="stHorizontalBlock"] button,
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-grp-marker) > [data-testid="stHorizontalBlock"] button {
            min-height: 2.5rem !important;
            font-weight: 700 !important;
            font-size: clamp(0.68rem, 2.9vw, 0.9rem) !important;
            padding-left: 0.2rem !important;
            padding-right: 0.2rem !important;
            white-space: nowrap !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-save-marker) > [data-testid="stHorizontalBlock"] button[kind="primary"] {
            min-height: 2.75rem !important;
            font-size: 1rem !important;
            font-weight: 800 !important;
        }
        @media (max-width: 768px) {
            div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
            [data-testid="stVerticalBlock"]:has(> div .ka-prog-save-marker) > [data-testid="stHorizontalBlock"] button,
            div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
            [data-testid="stVerticalBlock"]:has(> div .ka-prog-more-marker) > [data-testid="stHorizontalBlock"] button,
            div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
            [data-testid="stVerticalBlock"]:has(> div .ka-prog-copy-marker) > [data-testid="stHorizontalBlock"] button {
                min-height: 2.75rem !important;
                font-size: clamp(0.72rem, 3.2vw, 0.9rem) !important;
                white-space: nowrap !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _set_edit_group_idx(sk: str, idx: int) -> None:
    st.session_state[f"pgroup_pick_{sk}"] = idx


def _set_day_status(sk: str, group: str, status: str) -> None:
    st.session_state[f"pstatus_{sk}_{group}"] = status


def _render_group_picker(day_programs: list[dict], sk: str) -> tuple[int, dict, str]:
    """Always show 短跑 / 中長跑 / 跨欄 / 全部學員 on one row."""
    by_group = {
        normalize_group(p.get("group")): ensure_program_dict(p) for p in day_programs
    }
    pick_key = f"pgroup_pick_{sk}"
    if pick_key not in st.session_state:
        # Prefer first group that already has a saved program
        default_idx = 0
        for i, g in enumerate(GROUP_OPTIONS):
            if g in by_group:
                default_idx = i
                break
        st.session_state[pick_key] = default_idx
    cur = int(st.session_state[pick_key])
    if cur < 0 or cur >= len(GROUP_OPTIONS):
        cur = 0
        st.session_state[pick_key] = 0

    st.caption("切換要編輯的組別")
    with st.container():
        st.markdown(
            '<div class="ka-prog-grp-marker" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(len(GROUP_OPTIONS), gap="small")
        for i, (col, group) in enumerate(zip(cols, GROUP_OPTIONS)):
            with col:
                st.button(
                    group_display_label(group),
                    key=f"pgbtn_{sk}_{i}",
                    use_container_width=True,
                    type="primary" if i == cur else "secondary",
                    on_click=_set_edit_group_idx,
                    args=(sk, i),
                )

    edit_group = GROUP_OPTIONS[cur]
    if edit_group in by_group:
        prog = by_group[edit_group]
    else:
        prog = default_program(sk)
        prog["group"] = edit_group
        if not day_programs:
            st.caption("此日尚無課表，填寫跑案後按儲存即可。")
    return cur, prog, edit_group


def _render_day_status_picker(sk: str, edit_group: str, prog: dict) -> str:
    cur_type = normalize_train_type(prog["type"])
    options = ["訓練", "休息", "比賽"]
    default_status = (
        "比賽" if cur_type == "比賽" else "休息" if cur_type == "休息" else "訓練"
    )
    state_key = f"pstatus_{sk}_{edit_group}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_status
    current = st.session_state[state_key]
    if current not in options:
        current = default_status
        st.session_state[state_key] = current

    st.caption("當日安排")
    with st.container():
        st.markdown(
            '<div class="ka-prog-status-marker" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3, gap="small")
        with c1:
            st.button(
                "🏃 訓練",
                key=f"pstat_train_{sk}_{edit_group}",
                use_container_width=True,
                type="primary" if current == "訓練" else "secondary",
                on_click=_set_day_status,
                args=(sk, edit_group, "訓練"),
            )
        with c2:
            st.button(
                "😴 休息",
                key=f"pstat_rest_{sk}_{edit_group}",
                use_container_width=True,
                type="primary" if current == "休息" else "secondary",
                on_click=_set_day_status,
                args=(sk, edit_group, "休息"),
            )
        with c3:
            st.button(
                "🏁 比賽",
                key=f"pstat_comp_{sk}_{edit_group}",
                use_container_width=True,
                type="primary" if current == "比賽" else "secondary",
                on_click=_set_day_status,
                args=(sk, edit_group, "比賽"),
            )
    return st.session_state[state_key]


def _save_program(
    *,
    sk: str,
    edit_group: str,
    day_status: str,
    prog: dict,
    workout_text: str,
    tips: str,
    rpe: int,
    train_type: str,
    title: str,
) -> None:
    save_vol = (
        parse_workout_volume(workout_text)
        if day_status == "訓練"
        else {"total_meters": 0, "total_reps": 0}
    )
    save_program({
        "date": sk,
        "type": train_type,
        "title": title,
        "group": edit_group,
        "sets": 0,
        "reps": save_vol["total_reps"],
        "dist": save_vol["total_meters"],
        "rest": workout_text,
        "duration": int(round(estimate_workout_minutes(save_vol["total_meters"], train_type))),
        "rpe": rpe,
        "tips": tips,
        "phase": "",
        "week_theme": "",
        "target_seconds": 0,
        "exercises": "",
        "tech_focus": "",
        "field_event": "",
        "attempts": 0,
        "start_time": safe_str(prog.get("start_time")),
        "end_time": safe_str(prog.get("end_time")),
        "venue": safe_str(prog.get("venue")),
        "venue_other": safe_str(prog.get("venue_other")),
    })


def render_coach_day_editor(selected: date) -> None:
    """Mobile-friendly daily program editor for the selected calendar date."""
    inject_coach_editor_css()
    st.markdown('<div class="ka-prog-editor-root"></div>', unsafe_allow_html=True)

    sk = selected.isoformat()
    st.markdown(f"### ✏️ {format_timetable_date(sk)}")

    day_programs = get_programs_for_date(selected)

    _edit_idx, prog, edit_group = _render_group_picker(day_programs, sk)

    from utils.data_store import has_schedule_slot
    from utils.helpers import is_coach_plan_day

    if not is_coach_plan_day(prog if day_programs else None) and not has_schedule_slot(sk):
        st.warning(
            "此日未在「訓練時間表」排定時間／地點，或為休息日。"
            "請先到 **訓練時間表** 設定，或返回日曆選擇其他日子。"
        )

    sync = day_sync_status(prog if day_programs else None)
    tv_line = format_time_venue_line(prog) if day_programs else ""
    if tv_line:
        st.info(f"🕐 {tv_line}")
    hint = sync_status_label(sync)
    if hint and sync in ("need_workout", "need_schedule", "need_both"):
        (st.warning if sync == "need_workout" else st.info)(hint)

    day_status = _render_day_status_picker(sk, edit_group, prog)

    workout_text = ""
    tips = ""
    rpe = max(1, safe_int(prog.get("rpe"), 7))
    train_type = "休息"
    title = "休息"

    if day_status == "比賽":
        st.info("🏁 比賽日 — 儲存後日曆顯示「比賽」")
        train_type = title = "比賽"
    elif day_status == "休息":
        st.info("休息日 — 無訓練安排")
        train_type = title = "休息"
    else:
        train_type = "訓練"
        title = group_display_label(edit_group)

    def _render_save_actions() -> None:
        with st.container():
            st.markdown(
                '<div class="ka-prog-save-marker" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
            back_col, save_col, tpl_col = st.columns([1.1, 1.4, 1], gap="small")
            with back_col:
                if st.button(
                    "← 返回",
                    use_container_width=True,
                    key=f"pback_{sk}_{edit_group}",
                ):
                    st.session_state.coach_prog_screen = "cal"
                    st.rerun()
            with save_col:
                if st.button(
                    "💾 儲存",
                    type="primary",
                    use_container_width=True,
                    key=f"psave_{sk}_{edit_group}",
                ):
                    _save_program(
                        sk=sk,
                        edit_group=edit_group,
                        day_status=day_status,
                        prog=prog,
                        workout_text=workout_text,
                        tips=tips,
                        rpe=rpe,
                        train_type=train_type,
                        title=title,
                    )
                    st.session_state.coach_prog_screen = "cal"
                    st.session_state["prog_save_flash"] = f"已儲存 {short_group_label(edit_group)} 課表"
                    st.rerun()
            with tpl_col:
                if st.button("📁 範本", use_container_width=True, key=f"ptpl_{sk}_{edit_group}"):
                    tpl_vol = (
                        parse_workout_volume(workout_text)
                        if day_status == "訓練"
                        else {"total_meters": 0, "total_reps": 0}
                    )
                    save_as_template({
                        "type": train_type,
                        "title": title,
                        "group": edit_group,
                        "sets": 0,
                        "reps": tpl_vol["total_reps"],
                        "dist": tpl_vol["total_meters"],
                        "rest": workout_text,
                        "duration": int(round(estimate_workout_minutes(tpl_vol["total_meters"], train_type))),
                        "rpe": rpe,
                        "tips": tips,
                        "phase": "",
                        "week_theme": "",
                        "target_seconds": 0,
                        "exercises": "",
                        "tech_focus": "",
                        "field_event": "",
                        "attempts": 0,
                    })
                    st.success("已存範本")

    if day_status == "訓練":
        flash_key = f"pcopy_flash_{sk}_{edit_group}"
        flash = st.session_state.pop(flash_key, None)
        if flash:
            kind, msg = flash
            (st.success if kind == "success" else st.warning)(msg)

        # Apply「複製」from a history card into this editor
        apply_key = f"pcopy_apply_{sk}_{edit_group}"
        pending_copy = st.session_state.pop(apply_key, None)
        if isinstance(pending_copy, dict):
            _apply_workout_copy(sk, edit_group, pending_copy)
            st.session_state[flash_key] = ("success", "已帶入該日跑案，請確認後儲存")
            st.rerun()

        def _on_copy_week() -> None:
            _copy_last_week_same_day(sk, edit_group, selected)

        def _on_copy_prog(source: dict) -> None:
            st.session_state[apply_key] = dict(source)

        render_workout_history_compare(
            selected,
            highlight_group=edit_group,
            groups=[edit_group],
            on_copy_week=_on_copy_week,
            copy_week_key=f"pcopy_week_{sk}_{edit_group}",
            on_copy_program=_on_copy_prog,
        )

        workout_key = f"pworkout_{sk}_{edit_group}"
        tips_key = f"ptips_{sk}_{edit_group}"
        rpe_key = f"prpe_{sk}_{edit_group}"
        if workout_key not in st.session_state:
            st.session_state[workout_key] = saved_workout_text(prog) if day_programs else ""
        if tips_key not in st.session_state:
            st.session_state[tips_key] = saved_coach_tips(prog) if day_programs else ""
        if rpe_key not in st.session_state:
            st.session_state[rpe_key] = max(1, safe_int(prog.get("rpe"), 7))

        workout_text = st.text_area(
            "跑案詳情",
            height=150,
            placeholder=(
                "每行一段，例如：\n"
                "A. 6×200m @ 30\"  走200m恢復\n"
                "B. 4×400m @ 70\"  休息3分鐘"
            ),
            key=workout_key,
        )
        rpe = st.number_input("預期 RPE", 1, 10, key=rpe_key)
        tips = st.text_area(
            "教練備註",
            height=80,
            placeholder="選填",
            key=tips_key,
        )
        workout_text = st.session_state[workout_key]
        tips = st.session_state[tips_key]
        rpe = int(st.session_state[rpe_key])
        run_vol = parse_workout_volume(workout_text)
        if run_vol["total_meters"] > 0:
            est = estimate_workout_minutes(run_vol["total_meters"], train_type)
            st.caption(
                f"📊 總跑量 **{run_vol['total_meters']:,} m** · "
                f"**{run_vol['total_reps']}** 趟 · 約 **{est:.0f}** 分鐘"
            )
        _render_save_actions()
    else:
        _render_save_actions()

    if train_type not in ("比賽", "休息"):
        run_vol = parse_workout_volume(workout_text)
        load = calc_load(train_type, 0, rpe, total_meters=run_vol["total_meters"])
        athletes = get_student_names()
        acwr_v, _ = acwr_status(
            calc_acwr(get_all_logs(), athletes[0] if athletes else "", selected)
        )
        vol_note = f"{run_vol['total_meters']:,} m" if run_vol["total_meters"] else "—"
        st.caption(f"加權負荷 {load} · 跑量 {vol_note} · ACWR {acwr_v}")

    with st.container():
        st.markdown(
            '<div class="ka-prog-more-marker" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        m1, m2 = st.columns(2, gap="small")
        with m1:
            if st.button("🗑 刪除此組", use_container_width=True, key=f"pdelete_grp_{sk}_{edit_group}"):
                if program_exists(selected):
                    if delete_program(selected, group=edit_group):
                        st.success(f"已刪除 {short_group_label(edit_group)} 課表")
                        st.rerun()
                    st.info("找不到此組別課表")
                else:
                    st.info("此日沒有已儲存的課表")
        with m2:
            if st.button("🗑 刪除全日", use_container_width=True, key=f"pdelete_all_{sk}"):
                if program_exists(selected):
                    delete_program(selected)
                    st.success(f"已刪除 {sk} 全部課表")
                    st.rerun()
                else:
                    st.info("此日沒有已儲存的課表")

    with st.expander("📱 WhatsApp 課表文案"):
        per = load_periodization()
        targets = day_programs if day_programs else [prog]
        for p in targets:
            st.markdown(f"**{short_group_label(p.get('group'))}**")
            txt = whatsapp_program_text(
                {
                    **p,
                    "date": sk,
                    "title": p.get("title") or p.get("type"),
                    "type": normalize_train_type(safe_str(p.get("type"))),
                    "tips": p.get("tips") or tips,
                },
                per,
            )
            st.code(txt, language=None)

    with st.expander("📚 課表範本庫"):
        templates = load_templates()
        if templates.empty:
            st.write("尚無範本")
        else:
            for _, t in templates.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"{t['title']} · {short_group_label(t.get('group'))}")
                if c2.button("套用", key=f"tpl_{t['id']}_{edit_group}"):
                    apply_template(str(t["id"]), sk)
                    st.rerun()
                if c3.button("刪除", key=f"tpl_del_{t['id']}_{edit_group}"):
                    delete_template(str(t["id"]))
                    st.success("已刪除範本")
                    st.rerun()
