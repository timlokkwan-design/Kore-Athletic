"""Coach publish + student read — 最新消息."""
from __future__ import annotations

import streamlit as st

from utils.auth import get_current_user
from utils.data_store import (
    delete_announcement,
    get_announcements,
    publish_announcement,
    unpublish_announcement,
)
from utils.helpers import safe_str
from views.components.theme import render_empty_state


def _format_when(iso: str) -> str:
    text = safe_str(iso)
    if len(text) >= 16:
        return text[:16].replace("T", " ")
    return text or "—"


def render_coach_announcements() -> None:
    st.markdown("#### 發佈最新消息")
    st.caption("發佈後，學生平台「最新消息」會即時顯示。")

    user = get_current_user() or {}
    author = safe_str(user.get("name")) or "教練"

    title = st.text_input("標題", key="coach_news_title", placeholder="例如：本週訓練改期通知")
    body = st.text_area("內容", key="coach_news_body", height=140, placeholder="輸入要通知學生的內容…")
    if st.button("發佈", type="primary", use_container_width=True, key="coach_news_publish"):
        ok, msg = publish_announcement(title, body, author=author)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("##### 已發佈／草稿")
    try:
        items = get_announcements(published_only=False)
    except Exception as exc:
        st.error(
            "未能讀取最新消息資料表。請到 Supabase → SQL Editor 執行 "
            "`supabase/schema_patch_v202.sql`（建立 ka_announcements）。"
        )
        st.caption(str(exc))
        return
    if not items:
        render_empty_state("尚未有消息", "發佈第一則最新消息後會顯示於此")
        return

    for item in items:
        status = "已發佈" if item["published"] else "已取消發佈"
        with st.container(border=True):
            st.markdown(f"**{item['title']}** · {status}")
            st.caption(f"{_format_when(item['published_at'])} · {item['author'] or '教練'}")
            st.write(item["body"])
            c1, c2 = st.columns(2)
            if item["published"]:
                if c1.button("取消發佈", key=f"news_unpub_{item['id']}", use_container_width=True):
                    ok, msg = unpublish_announcement(item["id"])
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
            if c2.button("刪除", key=f"news_del_{item['id']}", use_container_width=True):
                ok, msg = delete_announcement(item["id"])
                st.success(msg) if ok else st.error(msg)
                st.rerun()


def render_student_announcements() -> None:
    st.markdown("#### 最新消息")
    st.caption("教練發佈的通知與公告。")
    try:
        items = get_announcements(published_only=True)
    except Exception:
        render_empty_state("暫時未能載入消息", "若剛更新 App，請教練於 Supabase 執行 schema_patch_v202.sql")
        return
    if not items:
        render_empty_state("暫無最新消息", "教練發佈後會顯示於此")
        return
    for item in items:
        with st.container(border=True):
            st.markdown(f"**{item['title']}**")
            st.caption(f"{_format_when(item['published_at'])} · {item['author'] or '教練'}")
            st.write(item["body"])


def render_latest_announcement_banner() -> None:
    """Compact teaser for student homepage."""
    try:
        items = get_announcements(published_only=True)
    except Exception:
        # Missing Supabase table / transient API errors must not blank the schedule tab.
        return
    if not items:
        return
    latest = items[0]
    preview = safe_str(latest.get("body"))
    if len(preview) > 80:
        preview = preview[:80] + "…"
    st.info(f"**最新消息：{latest['title']}**  \n{preview}")
