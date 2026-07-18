"""V6 login page."""

import streamlit as st

from utils.auth import login
from views.components.brand import render_auth_brand


def render_auth_view() -> None:
    render_auth_brand()

    st.subheader("登入帳號")
    col_l, col_r = st.columns([1, 1])
    with col_l:
        with st.form("login_form"):
            username = st.text_input("登入帳號", placeholder="輸入帳號")
            password = st.text_input("登入密碼", type="password")
            if st.form_submit_button("安全登入", type="primary", use_container_width=True):
                ok, msg = login(username, password)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
    with col_r:
        st.info(
            "**新學員**\n\n"
            "請點左側 **「註冊新學員」** 提交資料，"
            "待教練核准後即可登入。"
        )
        with st.expander("忘記密碼？"):
            st.caption(
                "**學員**：請聯絡教練，由教練在「隊伍管理 → 重設學員密碼」協助重設。\n\n"
                "**教練**：關閉系統後，在程式資料夾雙擊 **重設教練密碼.bat** "
                "（預設重設為 `ktll` / `170330`）。"
            )
