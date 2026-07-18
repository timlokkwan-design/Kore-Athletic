"""V6 註冊新學員 — 獨立頁面，免責條款用唯讀文字框顯示."""

from datetime import date

import streamlit as st

from utils.config import (
    GENDER_OPTIONS,
    HEALTH_DECLARATION_PLACEHOLDER,
    HKAAA_ID_PLACEHOLDER,
    HK_PERMANENT_OPTIONS,
    SPECIALTY_OPTIONS,
)
from utils.data_store import register_user
from utils.helpers import birth_fields_from_date, normalize_hkaaa_id
from views.components.brand import render_auth_brand

# V6 原文 — 直接寫在此檔，避免 import 問題
DISCLAIMER_FULL_TEXT = """【學生身體健康聲明及受傷免責條款】

1. 身體健康：確認報名學生身體狀況良好，無任何隱疾、心臟病、哮喘或不適宜進行劇烈田徑訓練之疾病。

2. 自負風險：明白田徑訓練涉及一定運動風險，本人自願讓子女參與並承擔相關風險。

3. 機構免責：對於學員因參與是次活動期間因意外、疏忽或不可抗力事件引致的任何個人傷亡或財物損失，主辦機構（KORE ATHLETIC）及教練團隊毋須承擔任何法律及經濟責任。

4. 緊急醫療：如遇緊急意外，授權主辦機構在無法即時聯絡家長的情況下，採取必要急救措施並安排送院，由此產生的醫療費用由家長自行承擔。

5. 遵守指引：學員必須嚴格遵守導師及運動場守則，如因不遵從指引引致意外，家長須承擔全部責任。
"""

AGREEMENT_LABEL = (
    "家長/監護人同意聲明：本人已仔細閱讀、完全明白並同意上述所有之內容。"
)


def render_register_view() -> None:
    render_auth_brand()
    st.caption("提交後需等待關添樂教練審批")

    st.error("⬇️ 請先閱讀以下條款，再填寫表單並勾選同意")
    st.markdown("### 學生身體健康聲明及受傷免責條款")
    st.text_area(
        "免責條款全文",
        value=DISCLAIMER_FULL_TEXT,
        height=220,
        disabled=True,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 基本資料")

    with st.form("register_form_v2"):
        st.markdown("**田徑報名基本資料**")
        r1, r2, r3 = st.columns(3)
        name = r1.text_input("中文名 *")
        name_en = r2.text_input("英文名 *")
        birth_date = r3.date_input(
            "出生年月日 *",
            value=date(2010, 1, 1),
            min_value=date(1950, 1, 1),
            max_value=date.today(),
            format="YYYY/MM/DD",
        )
        r4, r5, r6 = st.columns(3)
        gender = r4.selectbox("性別 *", GENDER_OPTIONS)
        hkaaa_id = r5.text_input("田總証編號 *", placeholder=HKAAA_ID_PLACEHOLDER)
        hk_pr = r6.selectbox("香港永久性居民 *", HK_PERMANENT_OPTIONS)

        st.markdown("**帳號及聯絡資料**")
        r7, r8, r9 = st.columns(3)
        reg_user = r7.text_input("登入帳號 *")
        reg_pass = r8.text_input("密碼 *", type="password")
        phone = r9.text_input("電話")
        r10, r11, r12 = st.columns(3)
        school = r10.text_input("學校")
        specialty = r11.selectbox("專項", SPECIALTY_OPTIONS)
        ec = r12.text_input("緊急聯絡人")
        ep = st.text_input("緊急電話")

        st.markdown("**學生健康狀況申報**")
        health = st.text_area(
            "健康申報",
            height=80,
            placeholder=HEALTH_DECLARATION_PLACEHOLDER,
            label_visibility="visible",
        )

        st.markdown("---")
        agree = st.checkbox(AGREEMENT_LABEL)

        if st.form_submit_button("提交註冊申請", type="primary", use_container_width=True):
            if not agree:
                st.error(
                    "請先閱讀「學生身體健康聲明及受傷免責條款」"
                    "並勾選「家長/監護人同意聲明」方能提交申請！"
                )
            elif not reg_user.strip() or not name.strip() or not name_en.strip():
                st.error("請填寫中文名、英文名及登入帳號")
            else:
                register_user({
                    "username": reg_user.strip(),
                    "name": name.strip(),
                    "name_en": name_en.strip(),
                    **birth_fields_from_date(birth_date),
                    "gender": gender,
                    "hkaaa_id": normalize_hkaaa_id(hkaaa_id),
                    "hk_permanent_resident": hk_pr,
                    "school": school,
                    "specialty": specialty,
                    "phone": phone,
                    "password": reg_pass,
                    "emergency_contact": ec,
                    "emergency_phone": ep,
                    "health": health.strip() or "無",
                    "child_name": "",
                    "role": "pending",
                })
                st.success("✅ 註冊已提交，等待關教練審批！")
                st.balloons()
