"""Visitor zone — public club info, no student private data."""
from __future__ import annotations

import streamlit as st

from utils.config import COACH_NAME
from utils.site_content import load_site_content
from views.components.contact_links import render_contact_block

VISITOR_SPECIALTIES = ["短跑", "中長跑", "跨欄"]


def render_visitor_view() -> None:
    content = load_site_content()
    st.markdown("### 訪客專區")
    st.caption("認識本會 · 如何加入")

    tab_about, tab_join = st.tabs(["認識本會", "如何加入"])

    with tab_about:
        st.markdown("##### 關於 KORE ATHLETIC")
        st.write(content.get("club_intro", ""))
        st.markdown("##### 教練團隊")
        st.write(content.get("coach_intro", ""))
        st.markdown("##### 訓練專項")
        st.write("、".join(VISITOR_SPECIALTIES))
        st.markdown("##### 聯絡方式")
        render_contact_block()

    with tab_join:
        st.markdown("##### 報名流程")
        for line in safe_lines(content.get("join_process", "")):
            st.markdown(line)
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 註冊新學員", type="primary", use_container_width=True, key="vis_goto_reg"):
                st.session_state.main_page = "註冊新學員"
                st.rerun()
        with c2:
            if st.button("🔑 登入", use_container_width=True, key="vis_goto_login"):
                st.session_state.main_page = "登入"
                st.rerun()

    st.caption(f"內部系統 · {COACH_NAME}教練田徑隊 · 訪客無法查看學員資料")


def safe_lines(text: str) -> list[str]:
    return [ln.strip() for ln in str(text or "").splitlines() if ln.strip()]
