"""V6 login page — mobile-first single column."""

import streamlit as st

from utils.auth import login
from views.components.brand import render_auth_brand
from views.components.contact_links import render_instagram_button


def render_auth_view() -> None:
    render_auth_brand(compact=True)

    st.subheader("登入帳號")
    with st.form("login_form"):
        username = st.text_input("登入帳號", placeholder="輸入帳號")
        password = st.text_input("登入密碼", type="password")
        if st.form_submit_button("安全登入", type="primary", use_container_width=True):
            ok, msg = login(username, password)
            if ok:
                st.rerun()
            else:
                st.error(msg)

    st.info(
        "**新學員** — 點選單（☰）→「註冊新學員」提交資料，"
        "待教練核准後即可登入。"
    )

    with st.expander("忘記密碼？"):
        st.caption(
            "請聯絡教練，由教練在「隊伍管理 → 重設學員密碼」協助重設。"
            "重設後請使用教練提供的新密碼登入。"
        )
        st.caption("亦可透過 Instagram 私信教練（不公開電話）。")
        render_instagram_button("📷 Instagram 聯絡教練", key="ig_auth_forgot")

    if st.button("← 返回訪客專區", use_container_width=True, key="auth_back_visitor"):
        st.session_state.main_page = "訪客專區"
        st.rerun()
