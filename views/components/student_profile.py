"""Student profile edit — registration fields."""
from __future__ import annotations

from datetime import date

import streamlit as st

from utils.auth import refresh_current_user
from utils.config import (
    GENDER_OPTIONS,
    HEALTH_DECLARATION_PLACEHOLDER,
    HKAAA_ID_PLACEHOLDER,
    HK_PERMANENT_OPTIONS,
)
from utils.data_store import get_avatar_path, remove_user_avatar, save_user_avatar, update_user_profile
from utils.helpers import birth_fields_from_date, default_birth_date, normalize_hkaaa_id, safe_str
from views.components.avatar import clear_avatar_cache, render_avatar
from views.components.specialty_change import render_specialty_change_request


def _render_avatar_upload(user: dict) -> None:
    st.markdown("#### 📷 個人頭像")
    st.caption("支援 JPG / PNG / WEBP，最大 2MB。頭像會顯示於側邊欄、排行榜及教練平台。")

    render_avatar(name=user["name"], username=user["username"], size=96)
    uploaded = st.file_uploader(
        "選擇頭像圖片",
        type=["png", "jpg", "jpeg", "webp"],
        key="student_avatar_upload",
    )
    if uploaded is not None:
        st.image(uploaded, caption="預覽", width=120)
        if st.button("確認上載頭像", type="primary", key="student_avatar_save", use_container_width=True):
            ok, msg = save_user_avatar(
                user["username"],
                uploaded.getvalue(),
                uploaded.type or "image/jpeg",
            )
            if ok:
                clear_avatar_cache()
                refresh_current_user()
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    if get_avatar_path(username=user["username"]):
        if st.button("移除頭像", key="student_avatar_remove", use_container_width=True):
            remove_user_avatar(user["username"])
            clear_avatar_cache()
            refresh_current_user()
            st.success("已移除頭像")
            st.rerun()


def render_student_profile(user: dict) -> None:
    _render_avatar_upload(user)
    st.markdown("---")
    st.markdown("#### 👤 個人資料")
    st.caption("可更新註冊時填寫的資料；專項更改需教練審批。")

    with st.form("student_profile_form"):
        st.markdown("**田徑報名基本資料**")
        name = st.text_input("中文名 *", value=safe_str(user.get("name")))
        name_en = st.text_input("英文名 *", value=safe_str(user.get("name_en")))
        birth_date = st.date_input(
            "出生年月日 *",
            value=default_birth_date(user),
            min_value=date(1950, 1, 1),
            max_value=date.today(),
            format="YYYY/MM/DD",
        )
        gender_idx = (
            GENDER_OPTIONS.index(user["gender"])
            if user.get("gender") in GENDER_OPTIONS
            else 0
        )
        gender = st.selectbox("性別 *", GENDER_OPTIONS, index=gender_idx)
        hkaaa_id = st.text_input(
            "田總証編號 *",
            value=safe_str(user.get("hkaaa_id")),
            placeholder=HKAAA_ID_PLACEHOLDER,
        )
        hk_pr_idx = (
            HK_PERMANENT_OPTIONS.index(user["hk_permanent_resident"])
            if user.get("hk_permanent_resident") in HK_PERMANENT_OPTIONS
            else 0
        )
        hk_pr = st.selectbox("香港永久性居民 *", HK_PERMANENT_OPTIONS, index=hk_pr_idx)

        st.markdown("**帳號及聯絡資料**")
        st.text_input("登入帳號", value=safe_str(user.get("username")), disabled=True)
        st.caption(f"目前專項：**{user.get('specialty') or '—'}**（更改請見下方）")
        phone = st.text_input("電話", value=safe_str(user.get("phone")))
        school = st.text_input("學校", value=safe_str(user.get("school")))
        new_password = st.text_input("新密碼（留空則不更改）", type="password")
        emergency_contact = st.text_input("緊急聯絡人", value=safe_str(user.get("emergency_contact")))
        emergency_phone = st.text_input("緊急電話", value=safe_str(user.get("emergency_phone")))

        st.markdown("**學生健康狀況申報**")
        health = st.text_area(
            "健康申報",
            value=safe_str(user.get("health")),
            height=80,
            placeholder=HEALTH_DECLARATION_PLACEHOLDER,
        )

        if st.form_submit_button("儲存個人資料", type="primary", use_container_width=True):
            if not name.strip() or not name_en.strip():
                st.error("請填寫中文名及英文名")
            else:
                payload = {
                    "name": name.strip(),
                    "name_en": name_en.strip(),
                    **birth_fields_from_date(birth_date),
                    "gender": gender,
                    "hkaaa_id": normalize_hkaaa_id(hkaaa_id),
                    "hk_permanent_resident": hk_pr,
                    "phone": phone.strip(),
                    "school": school.strip(),
                    "emergency_contact": emergency_contact.strip(),
                    "emergency_phone": emergency_phone.strip(),
                    "health": health.strip() or "無",
                }
                if new_password.strip():
                    payload["password"] = new_password.strip()
                update_user_profile(user["username"], payload)
                refresh_current_user()
                st.success("個人資料已更新")
                st.rerun()

    st.markdown("---")
    render_specialty_change_request(refresh_current_user() or user)
