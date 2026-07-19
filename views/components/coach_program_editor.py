"""Coach daily program editor — fixed 短跑 / 中長跑 / 其他 panels (no group switch)."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from utils.acwr import acwr_status, calc_acwr, calc_load, estimate_workout_minutes
from utils.config import (
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
from views.components.coach_mobile_ui import force_button_row
from views.components.coach_workout_compare import render_workout_history_compare

# Fixed edit slots — no group switcher.
# 1 短跑 · 2 中長跑 · 3 其他（跨欄／田項等，多數日子留空）
_PRIMARY_GROUPS = ("短跑組", "中長跑組")
_OTHER_GROUP = "跨欄組"
_EDIT_SLOTS: list[tuple[str, str, bool]] = [
    ("短跑組", "短跑", False),
    ("中長跑組", "中長跑", False),
    ("跨欄組", "其他", True),  # collapsed by default
]


def _apply_workout_copy(sk: str, edit_group: str, source: dict) -> None:
    """Fill editor widgets from a source program (after rerun)."""
    st.session_state[f"pworkout_{sk}_{edit_group}"] = saved_workout_text(source)
    st.session_state[f"ptips_{sk}_{edit_group}"] = saved_coach_tips(source)
    st.session_state[f"prpe_{sk}_{edit_group}"] = max(1, safe_int(source.get("rpe"), 7))


def _copy_last_week_same_day(sk: str, edit_group: str, selected: date) -> None:
    src_date = selected - timedelta(days=7)
    source = get_group_program_for_date(src_date, edit_group)
    label = short_group_label(edit_group)
    if not source:
        st.session_state[f"pcopy_flash_{sk}_{edit_group}"] = (
            "warn",
            f"上週同天（{format_timetable_date(src_date.isoformat())}）尚無 {label} 課表",
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
        f"已複製 {format_timetable_date(src_date.isoformat())} 的 {label} 跑案，請確認後儲存",
    )


def inject_coach_editor_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-status-marker) > [data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-save-marker) > [data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-more-marker) > [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.35rem !important;
            width: 100% !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-status-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-save-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"],
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-more-marker) > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 0 !important;
            flex: 1 1 0 !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-status-marker) > [data-testid="stHorizontalBlock"] button {
            min-height: 2.5rem !important;
            font-weight: 700 !important;
            font-size: clamp(0.68rem, 2.9vw, 0.9rem) !important;
            white-space: nowrap !important;
        }
        div[data-testid="stVerticalBlock"]:has(.ka-prog-editor-root)
        [data-testid="stVerticalBlock"]:has(> div .ka-prog-save-marker) > [data-testid="stHorizontalBlock"] button[kind="primary"] {
            min-height: 2.75rem !important;
            font-size: 1rem !important;
            font-weight: 800 !important;
        }
        .ka-prog-slot-title {
            font-weight: 800;
            font-size: 1.05rem;
            margin: 0.75rem 0 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _set_day_status(sk: str, status: str) -> None:
    st.session_state[f"pstatus_{sk}"] = status


def _prog_by_group(day_programs: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in day_programs:
        g = normalize_group(p.get("group"))
        out[g] = ensure_program_dict(p)
    return out


def _ref_prog(by_group: dict[str, dict], sk: str) -> dict:
    """Pick any saved program for shared time/venue / day-type hints."""
    for g in (*_PRIMARY_GROUPS, _OTHER_GROUP, "全體組員"):
        if g in by_group:
            return by_group[g]
    return default_program(sk)


def _render_day_status_picker(sk: str, ref_prog: dict) -> str:
    cur_type = normalize_train_type(ref_prog.get("type"))
    options = ["訓練", "休息", "比賽"]
    default_status = (
        "比賽" if cur_type == "比賽" else "休息" if cur_type == "休息" else "訓練"
    )
    state_key = f"pstatus_{sk}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_status
    current = st.session_state[state_key]
    if current not in options:
        current = default_status
        st.session_state[state_key] = current

    st.caption("當日安排（全組共用）")
    with force_button_row(key=f"prog_status_row_{sk}", n_cols=3) as cols:
        c1, c2, c3 = cols
        with c1:
            st.button(
                "🏃 訓練",
                key=f"pstat_train_{sk}",
                use_container_width=True,
                type="primary" if current == "訓練" else "secondary",
                on_click=_set_day_status,
                args=(sk, "訓練"),
            )
        with c2:
            st.button(
                "😴 休息",
                key=f"pstat_rest_{sk}",
                use_container_width=True,
                type="primary" if current == "休息" else "secondary",
                on_click=_set_day_status,
                args=(sk, "休息"),
            )
        with c3:
            st.button(
                "🏁 比賽",
                key=f"pstat_comp_{sk}",
                use_container_width=True,
                type="primary" if current == "比賽" else "secondary",
                on_click=_set_day_status,
                args=(sk, "比賽"),
            )
    return st.session_state[state_key]


def _save_group_program(
    *,
    sk: str,
    edit_group: str,
    day_status: str,
    ref_prog: dict,
    workout_text: str,
    tips: str,
    rpe: int,
) -> None:
    if day_status == "比賽":
        train_type = title = "比賽"
        workout_text = ""
    elif day_status == "休息":
        train_type = title = "休息"
        workout_text = ""
    else:
        train_type = "訓練"
        title = group_display_label(edit_group)

    save_vol = (
        parse_workout_volume(workout_text)
        if day_status == "訓練"
        else {"total_meters": 0, "total_reps": 0}
    )
    # Preserve time/venue from any existing day program (set in 訓練時間表)
    existing = get_group_program_for_date(sk, edit_group) or ref_prog
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
        "start_time": safe_str(existing.get("start_time")),
        "end_time": safe_str(existing.get("end_time")),
        "venue": safe_str(existing.get("venue")),
        "venue_other": safe_str(existing.get("venue_other")),
    })


def _init_slot_state(sk: str, group: str, prog: dict | None) -> None:
    workout_key = f"pworkout_{sk}_{group}"
    tips_key = f"ptips_{sk}_{group}"
    rpe_key = f"prpe_{sk}_{group}"
    if workout_key not in st.session_state:
        st.session_state[workout_key] = saved_workout_text(prog) if prog else ""
    if tips_key not in st.session_state:
        st.session_state[tips_key] = saved_coach_tips(prog) if prog else ""
    if rpe_key not in st.session_state:
        st.session_state[rpe_key] = max(1, safe_int((prog or {}).get("rpe"), 7))


def _render_group_slot(
    selected: date,
    sk: str,
    group: str,
    label: str,
    prog: dict | None,
    *,
    collapsed: bool = False,
) -> dict:
    """Render one group's workout fields; return widget values."""
    _init_slot_state(sk, group, prog)

    flash_key = f"pcopy_flash_{sk}_{group}"
    flash = st.session_state.pop(flash_key, None)
    if flash:
        kind, msg = flash
        (st.success if kind == "success" else st.warning)(msg)

    apply_key = f"pcopy_apply_{sk}_{group}"
    pending = st.session_state.pop(apply_key, None)
    if isinstance(pending, dict):
        _apply_workout_copy(sk, group, pending)
        st.session_state[flash_key] = ("success", f"已帶入{label}跑案，請確認後儲存")
        st.rerun()

    def _body() -> dict:
        def _on_copy_week() -> None:
            _copy_last_week_same_day(sk, group, selected)

        def _on_copy_prog(source: dict) -> None:
            st.session_state[apply_key] = dict(source)

        with st.expander(f"📊 近2週 · {label} 參考", expanded=False):
            render_workout_history_compare(
                selected,
                highlight_group=group,
                groups=[group],
                show_heading=False,
                on_copy_week=_on_copy_week,
                copy_week_key=f"pcopy_week_{sk}_{group}",
                on_copy_program=_on_copy_prog,
            )

        workout_key = f"pworkout_{sk}_{group}"
        tips_key = f"ptips_{sk}_{group}"
        rpe_key = f"prpe_{sk}_{group}"
        st.text_area(
            f"{label} · 跑案詳情",
            height=140,
            placeholder=(
                "每行一段，例如：\n"
                "A. 6×200m @ 30\"  走200m恢復\n"
                "B. 4×400m @ 70\"  休息3分鐘"
            ),
            key=workout_key,
        )
        st.number_input(f"{label} · 預期 RPE", 1, 10, key=rpe_key)
        st.text_area(
            f"{label} · 教練備註",
            height=70,
            placeholder="選填",
            key=tips_key,
        )
        workout_text = str(st.session_state.get(workout_key) or "")
        tips = str(st.session_state.get(tips_key) or "")
        rpe = int(st.session_state.get(rpe_key) or 7)
        run_vol = parse_workout_volume(workout_text)
        if run_vol["total_meters"] > 0:
            est = estimate_workout_minutes(run_vol["total_meters"], "訓練")
            st.caption(
                f"📊 總跑量 **{run_vol['total_meters']:,} m** · "
                f"**{run_vol['total_reps']}** 趟 · 約 **{est:.0f}** 分鐘"
            )
        return {
            "group": group,
            "label": label,
            "workout_text": workout_text,
            "tips": tips,
            "rpe": rpe,
            "has_content": bool(workout_text.strip() or tips.strip()),
        }

    st.markdown(
        f"<div class='ka-prog-slot-title'>✏️ {label}</div>",
        unsafe_allow_html=True,
    )
    if collapsed:
        # Expand if this group already has saved content
        has_saved = bool(prog and (saved_workout_text(prog) or saved_coach_tips(prog)))
        with st.expander(
            "選填 — 多數日子可留空（跨欄／田項等）",
            expanded=has_saved,
        ):
            return _body()
    return _body()


def render_coach_day_editor(selected: date) -> None:
    """Edit 短跑 + 中長跑 (+ optional 其他) on one screen — no group switcher."""
    inject_coach_editor_css()
    st.markdown('<div class="ka-prog-editor-root"></div>', unsafe_allow_html=True)

    sk = selected.isoformat()
    st.markdown(f"### ✏️ {format_timetable_date(sk)}")
    st.caption("固定填寫 **短跑**、**中長跑**；**其他** 多數日子唔使填。")

    day_programs = get_programs_for_date(selected)
    by_group = _prog_by_group(day_programs)
    ref_prog = _ref_prog(by_group, sk)

    from utils.data_store import has_schedule_slot
    from utils.helpers import is_coach_plan_day

    if not is_coach_plan_day(ref_prog if day_programs else None) and not has_schedule_slot(sk):
        st.warning(
            "此日未在「訓練時間表」排定時間／地點，或為休息日。"
            "請先到 **訓練時間表** 設定，或返回日曆選擇其他日子。"
        )

    sync = day_sync_status(ref_prog if day_programs else None)
    tv_line = format_time_venue_line(ref_prog) if day_programs else ""
    if tv_line:
        st.info(f"🕐 {tv_line}")
    hint = sync_status_label(sync)
    if hint and sync in ("need_workout", "need_schedule", "need_both"):
        (st.warning if sync == "need_workout" else st.info)(hint)

    day_status = _render_day_status_picker(sk, ref_prog)
    slot_values: list[dict] = []

    if day_status == "比賽":
        st.info("🏁 比賽日 — 儲存後短跑／中長跑皆標示「比賽」")
    elif day_status == "休息":
        st.info("休息日 — 儲存後短跑／中長跑皆標示「休息」")
    else:
        for group, label, collapsed in _EDIT_SLOTS:
            prog = by_group.get(group)
            slot_values.append(
                _render_group_slot(
                    selected,
                    sk,
                    group,
                    label,
                    prog,
                    collapsed=collapsed,
                )
            )

    # 返回｜儲存｜範本 — force one equal row on mobile
    with force_button_row(key=f"prog_save_row_{sk}", n_cols=3) as cols:
        back_col, save_col, tpl_col = cols
        with back_col:
            if st.button("← 返回", use_container_width=True, key=f"pback_{sk}"):
                st.session_state.coach_prog_screen = "cal"
                st.rerun()
        with save_col:
            if st.button(
                "💾 儲存",
                type="primary",
                use_container_width=True,
                key=f"psave_all_{sk}",
            ):
                saved_labels: list[str] = []
                if day_status in ("休息", "比賽"):
                    # Persist day type on primary groups (and other if already exists)
                    targets = list(_PRIMARY_GROUPS)
                    if _OTHER_GROUP in by_group or "全體組員" in by_group:
                        targets.append(_OTHER_GROUP)
                    for g in targets:
                        _save_group_program(
                            sk=sk,
                            edit_group=g,
                            day_status=day_status,
                            ref_prog=ref_prog,
                            workout_text="",
                            tips="",
                            rpe=7,
                        )
                        saved_labels.append(short_group_label(g))
                else:
                    for slot in slot_values:
                        g = slot["group"]
                        # Always save primary groups; other only if filled or already existed
                        if g == _OTHER_GROUP and not slot["has_content"] and g not in by_group:
                            continue
                        if g == _OTHER_GROUP and not slot["has_content"] and g in by_group:
                            # Clear optional other when emptied
                            delete_program(selected, group=g)
                            continue
                        _save_group_program(
                            sk=sk,
                            edit_group=g,
                            day_status=day_status,
                            ref_prog=ref_prog,
                            workout_text=slot["workout_text"],
                            tips=slot["tips"],
                            rpe=slot["rpe"],
                        )
                        saved_labels.append(slot["label"])
                st.session_state.coach_prog_screen = "cal"
                st.session_state["prog_save_flash"] = (
                    f"已儲存：{'、'.join(saved_labels)}" if saved_labels else "已儲存課表"
                )
                st.rerun()
        with tpl_col:
            if st.button(
                "📁 範本",
                use_container_width=True,
                key=f"ptpl_menu_{sk}",
                help="將第一個有內容的組別（優先短跑）存為範本",
            ):
                src = next(
                    (s for s in slot_values if s.get("has_content")),
                    slot_values[0] if slot_values else None,
                )
                if not src or not src.get("workout_text", "").strip():
                    st.warning("請先填寫跑案再存範本")
                else:
                    vol = parse_workout_volume(src["workout_text"])
                    save_as_template({
                        "type": "訓練",
                        "title": src["label"],
                        "group": src["group"],
                        "sets": 0,
                        "reps": vol["total_reps"],
                        "dist": vol["total_meters"],
                        "rest": src["workout_text"],
                        "duration": int(
                            round(estimate_workout_minutes(vol["total_meters"], "訓練"))
                        ),
                        "rpe": src["rpe"],
                        "tips": src["tips"],
                        "phase": "",
                        "week_theme": "",
                        "target_seconds": 0,
                        "exercises": "",
                        "tech_focus": "",
                        "field_event": "",
                        "attempts": 0,
                    })
                    st.success(f"已將「{src['label']}」存為範本")

    if day_status == "訓練" and slot_values:
        # Lightweight load hint from 短跑 if present
        sprint = next((s for s in slot_values if s["group"] == "短跑組"), None)
        if sprint and sprint["workout_text"].strip():
            run_vol = parse_workout_volume(sprint["workout_text"])
            load = calc_load("訓練", 0, sprint["rpe"], total_meters=run_vol["total_meters"])
            athletes = get_student_names()
            acwr_v, _ = acwr_status(
                calc_acwr(get_all_logs(), athletes[0] if athletes else "", selected)
            )
            vol_note = f"{run_vol['total_meters']:,} m" if run_vol["total_meters"] else "—"
            st.caption(f"短跑負荷參考 {load} · 跑量 {vol_note} · ACWR {acwr_v}")

    with st.container():
        st.markdown(
            '<div class="ka-prog-more-marker" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        if st.button("🗑 刪除當日全部課表", use_container_width=True, key=f"pdelete_all_{sk}"):
            if program_exists(selected):
                delete_program(selected)
                st.success(f"已刪除 {sk} 全部課表")
                st.session_state.coach_prog_screen = "cal"
                st.rerun()
            else:
                st.info("此日沒有已儲存的課表")

    with st.expander("📱 WhatsApp 課表文案"):
        per = load_periodization()
        targets = day_programs if day_programs else [ref_prog]
        for p in targets:
            st.markdown(f"**{short_group_label(p.get('group'))}**")
            txt = whatsapp_program_text(
                {
                    **p,
                    "date": sk,
                    "title": p.get("title") or p.get("type"),
                    "type": normalize_train_type(safe_str(p.get("type"))),
                    "tips": p.get("tips") or "",
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
                if c2.button("套用", key=f"tpl_{t['id']}_{sk}"):
                    apply_template(str(t["id"]), sk)
                    st.rerun()
                if c3.button("刪除", key=f"tpl_del_{t['id']}_{sk}"):
                    delete_template(str(t["id"]))
                    st.success("已刪除範本")
                    st.rerun()
