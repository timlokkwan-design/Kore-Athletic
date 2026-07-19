"""Coach competition registration sheet."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.config import EVENTS
from utils.data_store import (
    add_competition,
    build_comp_export_df,
    delete_competition,
    ensure_youth_age_group_v_registrations,
    get_comp_entries_for_comp,
    get_competitions,
    next_registration_candidate,
    registration_status,
    registration_status_label,
    resolve_event_pb,
    update_competition,
)
from utils.helpers import safe_str
from views.components.avatar import render_person
from views.components.comp_roster import render_successful_registration_roster


def _events_text(events: list[str]) -> str:
    return "、".join(events) if events else "—"


def _parse_deadline(value: str) -> date | None:
    text = safe_str(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def render_coach_comp_registration() -> None:
    ensure_youth_age_group_v_registrations()
    st.subheader("📋 比賽報名表")
    st.caption(
        "設定比賽及開放項目；學生自行選項報名。"
        "必須填寫「報名截止」後學生方可報名；過期後不能報名，再為下一個比賽填寫截止日期即可開放。"
    )

    comps = get_competitions()
    today = date.today().isoformat()

    if comps:
        summary_rows = []
        for comp in comps:
            status = registration_status(comp, today=today)
            summary_rows.append({
                "比賽": comp["name"],
                "日期": comp["date"],
                "地點": comp["location"] or "—",
                "項目": _events_text(comp["events"]),
                "報名截止": comp.get("deadline") or "待填寫",
                "報名狀態": registration_status_label(status),
                "報名人數": comp.get("registration_count", 0),
                "發布": "✅" if comp["published"] else "—",
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        next_comp = next_registration_candidate(comps, today=today)
        if next_comp:
            st.info(
                f"下一個待開放報名：**{next_comp['name']}**（{next_comp.get('date') or '—'}）。"
                f"請在下方管理區填寫「報名截止」日期後，學生即可報名。"
            )

        # Roster summary first — mobile users must see who registered without digging into editors.
        st.markdown("#### ✅ 成功報名名單")
        any_roster = False
        for comp in comps:
            entries = get_comp_entries_for_comp(comp["id"])
            count = len(entries)
            if count:
                any_roster = True
            status = registration_status(comp, today=today)
            with st.expander(
                f"{comp['name']} · {comp['date']} · {count} 人 · {registration_status_label(status)}",
                expanded=count > 0,
            ):
                render_successful_registration_roster(comp["id"])
        if not any_roster:
            st.caption("暫未有成功報名；學生提交後會顯示於此。")

    st.markdown("---")
    st.markdown("#### ➕ 新增比賽")

    with st.form("coach_comp_reg_new"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("比賽名稱", placeholder="校際田徑錦標賽")
            comp_date = st.date_input("比賽日期", value=date.today())
            location = st.text_input("比賽地點", placeholder="灣仔運動場")
            events = st.multiselect("開放報名項目", EVENTS, key="coach_comp_reg_events_new")
        with c2:
            set_deadline = st.checkbox(
                "設定報名截止日期（勾選後學生方可報名；不勾則有待稍後填寫）",
                value=False,
                key="coach_comp_reg_set_deadline_new",
            )
            deadline = st.date_input(
                "報名截止",
                value=date.today(),
                key="coach_comp_reg_deadline_new",
            )
            link = st.text_input("比賽連結", placeholder="https://...")
            notes = st.text_area("須知 / 備註", placeholder="請準時提交報名資料")
        published = st.checkbox("發布至學生平台", value=True)
        if st.form_submit_button("新增比賽", type="primary"):
            if not name.strip():
                st.error("請填寫比賽名稱")
            elif not events:
                st.error("請至少選擇一個開放項目")
            else:
                add_competition({
                    "name": name.strip(),
                    "date": comp_date.isoformat(),
                    "event": ",".join(events),
                    "location": location.strip(),
                    "registered": "",
                    "deadline": deadline.isoformat() if set_deadline else "",
                    "assembly_time": "",
                    "transport": "",
                    "notes": notes.strip(),
                    "link": link.strip(),
                    "published": "1" if published else "0",
                })
                st.success(
                    "已新增比賽"
                    + ("；報名已開放至截止日。" if set_deadline else "。截止日期有待填寫，學生暫未能報名。")
                )
                st.rerun()

    st.markdown("---")
    st.markdown("#### ✏️ 管理現有比賽")

    if not comps:
        st.info("尚未設定任何比賽。")
        return

    for comp in comps:
        count = comp.get("registration_count", 0)
        status = registration_status(comp, today=today)
        status_label = registration_status_label(status)
        # Only auto-expand the next pending-deadline meet (or first with roster) —
        # expanding every form on mobile made content look "empty" under the dock.
        auto_open = (status == "pending_deadline" and next_comp and next_comp["id"] == comp["id"]) or (
            count > 0 and status == "open"
        )
        with st.expander(
            f"{comp['name']} · {comp['date']} · 報名 {count} 人 · {status_label}",
            expanded=auto_open,
        ):
            st.markdown(f"**報名狀態：** {status_label}")
            if status == "pending_deadline":
                st.caption("尚未填寫截止日 → 學生暫未能報名。填寫並儲存後即開放。")
            elif status == "closed":
                st.caption("已過截止日 → 學生不能再報名。可為下一個比賽設定截止日以開放報名。")

            edit_name = st.text_input("比賽名稱", comp["name"], key=f"comp_name_{comp['id']}")
            edit_date = st.date_input(
                "比賽日期",
                value=date.fromisoformat(comp["date"]) if comp["date"] else date.today(),
                key=f"comp_date_{comp['id']}",
            )
            edit_location = st.text_input("地點", comp["location"], key=f"comp_loc_{comp['id']}")
            edit_events = st.multiselect(
                "開放報名項目",
                EVENTS,
                default=comp["events"],
                key=f"comp_events_{comp['id']}",
            )
            existing_deadline = _parse_deadline(comp.get("deadline") or "")
            set_deadline = st.checkbox(
                "已設定報名截止日期（學生方可報名）",
                value=existing_deadline is not None,
                key=f"comp_set_deadline_{comp['id']}",
            )
            edit_deadline = st.date_input(
                "報名截止",
                value=existing_deadline or date.today(),
                key=f"comp_deadline_{comp['id']}",
                disabled=not set_deadline,
            )
            edit_link = st.text_input("比賽連結", comp.get("link", ""), key=f"comp_link_{comp['id']}")
            edit_notes = st.text_area("須知 / 備註", comp.get("notes", ""), key=f"comp_notes_{comp['id']}")
            edit_published = st.checkbox(
                "發布至學生平台",
                value=comp["published"],
                key=f"comp_pub_{comp['id']}",
            )

            b1, b2 = st.columns(2)
            if b1.button("儲存", type="primary", key=f"comp_save_{comp['id']}"):
                update_competition(comp["id"], {
                    "name": edit_name.strip(),
                    "date": edit_date.isoformat(),
                    "event": ",".join(edit_events),
                    "location": edit_location.strip(),
                    "deadline": edit_deadline.isoformat() if set_deadline else "",
                    "link": edit_link.strip(),
                    "notes": edit_notes.strip(),
                    "published": "1" if edit_published else "0",
                })
                st.success("已更新")
                st.rerun()
            if b2.button("刪除", key=f"comp_del_{comp['id']}"):
                delete_competition(comp["id"])
                st.success("已刪除")
                st.rerun()

            export_df = build_comp_export_df(comp["id"])
            if not export_df.empty:
                st.download_button(
                    "⬇️ 匯出比賽報名 CSV",
                    data=export_df.to_csv(index=False, encoding="utf-8-sig"),
                    file_name=f"比賽報名_{comp['name']}_{comp['date']}.csv",
                    mime="text/csv",
                    key=f"comp_export_{comp['id']}",
                )
                st.dataframe(export_df, use_container_width=True, hide_index=True)
            else:
                st.caption("尚無學生報名，或學生尚未選擇項目。")

            entries = get_comp_entries_for_comp(comp["id"])
            render_successful_registration_roster(comp["id"])
            if entries:
                st.markdown("**報名詳情（PB）**")
                for entry in entries:
                    render_person(
                        entry["athlete_name"],
                        subtitle=(
                            f"{_events_text(entry['events'])} "
                            f"（{entry['submitted_at'][:16] if entry.get('submitted_at') else ''}）"
                        ),
                        username=entry.get("username"),
                        size=36,
                    )
                    for event in entry["events"]:
                        pb = resolve_event_pb(entry["athlete_name"], event, entry.get("event_pbs"))
                        st.caption(
                            f"  └ {event}：{pb.get('score') or '—'} "
                            f"（{pb.get('comp_name') or '—'} · {pb.get('date') or '—'}）"
                        )

            if comp.get("link"):
                st.markdown(f"🔗 [比賽連結]({comp['link']})")

    # Space so last expander content is not hidden under the fixed dock
    st.markdown('<div style="height:5rem"></div>', unsafe_allow_html=True)
