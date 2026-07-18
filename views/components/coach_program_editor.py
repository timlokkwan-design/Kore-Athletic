"""Coach daily program editor — mobile-friendly layout."""

from __future__ import annotations

from datetime import date

import streamlit as st

from utils.acwr import acwr_status, calc_acwr, calc_load, estimate_workout_minutes
from utils.config import GROUP_OPTIONS, default_program, group_display_label, normalize_train_type
from utils.data_store import (
    apply_template,
    delete_program,
    delete_template,
    ensure_program_dict,
    get_all_logs,
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
    sync_status_label,
    whatsapp_program_text,
    workout_detail,
)
from views.components.coach_workout_compare import render_workout_history_compare


def inject_coach_editor_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root) [data-testid="stVerticalBlock"]:has(.ka-prog-status-marker) button,
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root) [data-testid="stVerticalBlock"]:has(.ka-prog-grp-marker) button {
            min-height: 2.5rem !important;
            font-weight: 700 !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root) [data-testid="stVerticalBlock"]:has(.ka-prog-save-marker) button[kind="primary"] {
            min-height: 2.75rem !important;
            font-size: 1rem !important;
            font-weight: 800 !important;
        }
        @media (max-width: 768px) {
            div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root) {
                padding-bottom: 4.5rem;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root) [data-testid="stVerticalBlock"]:has(.ka-prog-save-marker) {
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 999;
                background: var(--background-color, #ffffff);
                border-top: 1px solid #e2e8f0;
                padding: 0.5rem 0.75rem calc(0.5rem + env(safe-area-inset-bottom, 0px));
                margin: 0 !important;
                box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.08);
            }
            div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root) [data-testid="stVerticalBlock"]:has(.ka-prog-save-marker) [data-testid="column"] {
                padding-left: 0.25rem !important;
                padding-right: 0.25rem !important;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root) [data-testid="stVerticalBlock"]:has(.ka-prog-more-marker) [data-testid="column"] {
                flex: 1 1 48% !important;
                min-width: 48% !important;
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
    if not day_programs:
        edit_group = st.selectbox(
            "組別",
            GROUP_OPTIONS,
            format_func=group_display_label,
            key=f"pgroup_new_{sk}",
        )
        prog = default_program(sk)
        prog["group"] = edit_group
        st.caption("此日尚無課表，選擇組別後填寫跑案並儲存。")
        return -1, prog, edit_group

    group_labels = [group_display_label(p.get("group")) for p in day_programs]
    pick_key = f"pgroup_pick_{sk}"
    if pick_key not in st.session_state:
        st.session_state[pick_key] = 0
    cur = int(st.session_state[pick_key])
    if cur >= len(day_programs):
        cur = 0
        st.session_state[pick_key] = 0

    if len(day_programs) == 1:
        st.markdown(f"**👥 {group_labels[0]}**")
    else:
        st.caption("切換要編輯的組別")
        st.markdown('<div class="ka-prog-grp-marker"></div>', unsafe_allow_html=True)
        cols = st.columns(len(day_programs))
        for i, (col, label) in enumerate(zip(cols, group_labels)):
            with col:
                st.button(
                    label,
                    key=f"pgbtn_{sk}_{i}",
                    use_container_width=True,
                    type="primary" if i == cur else "secondary",
                    on_click=_set_edit_group_idx,
                    args=(sk, i),
                )
    prog = ensure_program_dict(day_programs[cur])
    return cur, prog, safe_str(prog.get("group"))


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
    st.markdown('<div class="ka-prog-status-marker"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
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
    existing_groups = {safe_str(p.get("group")) for p in day_programs}
    available_groups = [g for g in GROUP_OPTIONS if g not in existing_groups]

    _edit_idx, prog, edit_group = _render_group_picker(day_programs, sk)

    if available_groups:
        with st.expander("➕ 新增其他組別訓練", expanded=False):
            new_group = st.selectbox(
                "組別",
                available_groups,
                format_func=group_display_label,
                key=f"padd_grp_{sk}",
            )
            if st.button("新增組別", key=f"padd_btn_{sk}", use_container_width=True):
                draft = default_program(sk)
                draft["group"] = new_group
                draft["type"] = "休息"
                draft["title"] = "休息"
                save_program(draft)
                st.success(f"已新增 {short_group_label(new_group)} 課表")
                st.rerun()

    sync = day_sync_status(prog if day_programs else None)
    tv_line = format_time_venue_line(prog) if day_programs else ""
    if tv_line:
        st.info(f"🕐 {tv_line}")
    hint = sync_status_label(sync)
    if hint and sync in ("need_workout", "need_schedule", "need_both"):
        (st.warning if sync == "need_workout" else st.info)(hint)

    day_status = _render_day_status_picker(sk, edit_group, prog)

    workout_text = ""
    tips = safe_str(prog.get("tips"))
    rpe = max(1, safe_int(prog.get("rpe"), 7))
    train_type = "休息"
    title = "休息"

    if day_status == "比賽":
        st.info("🏁 比賽日 — 儲存後月曆顯示「比賽」")
        train_type = title = "比賽"
    elif day_status == "休息":
        st.info("休息日 — 無訓練安排")
        train_type = title = "休息"
    else:
        workout_text = st.text_area(
            "跑案詳情",
            value=workout_detail(prog),
            height=150,
            placeholder=(
                "每行一段，例如：\n"
                "A. 6×200m @ 30\"  走200m恢復\n"
                "B. 4×400m @ 70\"  休息3分鐘"
            ),
            key=f"pworkout_{sk}_{edit_group}",
        )
        rpe = st.number_input(
            "預期 RPE",
            1,
            10,
            rpe,
            key=f"prpe_{sk}_{edit_group}",
        )
        tips = st.text_area(
            "教練備註",
            tips,
            height=80,
            key=f"ptips_{sk}_{edit_group}",
        )
        train_type = "訓練"
        title = group_display_label(edit_group)
        run_vol = parse_workout_volume(workout_text)
        if run_vol["total_meters"] > 0:
            est = estimate_workout_minutes(run_vol["total_meters"], train_type)
            st.caption(
                f"📊 總跑量 **{run_vol['total_meters']:,} m** · "
                f"**{run_vol['total_reps']}** 趟 · 約 **{est:.0f}** 分鐘"
            )

    if train_type not in ("比賽", "休息"):
        run_vol = parse_workout_volume(workout_text)
        load = calc_load(train_type, 0, rpe, total_meters=run_vol["total_meters"])
        athletes = get_student_names()
        acwr_v, _ = acwr_status(
            calc_acwr(get_all_logs(), athletes[0] if athletes else "", selected)
        )
        vol_note = f"{run_vol['total_meters']:,} m" if run_vol["total_meters"] else "—"
        st.caption(f"加權負荷 {load} · 跑量 {vol_note} · ACWR {acwr_v}")

    st.markdown('<div class="ka-prog-save-marker"></div>', unsafe_allow_html=True)
    s1, s2 = st.columns([2, 1])
    with s1:
        if st.button(
            "💾 儲存課表",
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
            st.success(f"已儲存 {short_group_label(edit_group)} 課表")
            st.rerun()
    with s2:
        if st.button("📁 存範本", use_container_width=True, key=f"ptpl_{sk}_{edit_group}"):
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

    st.markdown('<div class="ka-prog-more-marker"></div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    with m1:
        if st.button("🗑 刪除此組別", use_container_width=True, key=f"pdelete_grp_{sk}_{edit_group}"):
            if program_exists(selected):
                if delete_program(selected, group=edit_group):
                    st.success(f"已刪除 {short_group_label(edit_group)} 課表")
                    st.rerun()
                st.info("找不到此組別課表")
            else:
                st.info("此日沒有已儲存的課表")
    with m2:
        if st.button("🗑 刪除當日全部", use_container_width=True, key=f"pdelete_all_{sk}"):
            if program_exists(selected):
                delete_program(selected)
                st.success(f"已刪除 {sk} 全部課表")
                st.rerun()
            else:
                st.info("此日沒有已儲存的課表")

    with st.expander(
        f"📊 近2週 · {group_display_label(edit_group)} 跑案參考",
        expanded=(day_status == "訓練"),
    ):
        st.caption("7 格一列 · 點方格放大檢視")
        render_workout_history_compare(
            selected,
            highlight_group=edit_group,
            groups=[edit_group],
            show_heading=False,
        )

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
