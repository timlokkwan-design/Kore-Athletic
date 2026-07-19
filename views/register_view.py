"""V6 註冊新學員 — 分步表單 + 提交成功頁."""

from datetime import date, datetime

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
from views.components.contact_links import render_instagram_button

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


def _init_register_draft() -> None:
    if "register_draft" not in st.session_state:
        st.session_state.register_draft = {
            "name": "",
            "name_en": "",
            "birth_date": date(2010, 1, 1),
            "gender": GENDER_OPTIONS[0],
            "hkaaa_id": "",
            "hk_pr": HK_PERMANENT_OPTIONS[0],
            "reg_user": "",
            "reg_pass": "",
            "phone": "",
            "school": "",
            "specialty": SPECIALTY_OPTIONS[0],
            "ec": "",
            "ep": "",
            "health": "",
        }
    if "register_step" not in st.session_state:
        st.session_state.register_step = 1
    if "register_submitted" not in st.session_state:
        st.session_state.register_submitted = False


def _set_register_step(step: int) -> None:
    st.session_state.register_step = step


def _render_success_page(submitted_at: str, username: str, name: str = "", specialty: str = "") -> None:
    st.success("✅ 註冊申請已成功提交")
    st.markdown("#### 待教練審批")
    st.markdown(
        f"- **提交時間**：{submitted_at}\n"
        f"- **登入帳號**：`{username}`\n"
        "- **狀態**：等待教練核准\n"
        "- **下一步**：核准後可使用帳號登入學生平台"
    )
    st.info(
        "教練會在**系統內**審批你的申請。"
        "核准後請用上方帳號登入；一般需數日內完成，無需另行致電。"
    )
    st.markdown("---")
    st.caption("一般查詢（非催審批）可透過 Instagram 聯絡本會：")
    render_instagram_button("📷 Instagram", key="ig_reg_status")
    if st.button("返回登入", type="primary", use_container_width=True, key="reg_goto_login"):
        st.session_state.main_page = "登入"
        st.session_state.register_submitted = False
        st.session_state.register_step = 1
        st.rerun()


def render_register_view() -> None:
    _init_register_draft()
    if st.session_state.register_submitted:
        info = st.session_state.get("register_success_info", {})
        _render_success_page(
            info.get("time", ""),
            info.get("username", ""),
            name=info.get("name", ""),
            specialty=info.get("specialty", ""),
        )
        return

    render_auth_brand(compact=True)
    step = int(st.session_state.register_step)
    draft = st.session_state.register_draft

    st.progress(step / 3, text=f"步驟 {step} / 3")
    st.caption("提交後需等待關教練審批")

    if step == 1:
        st.markdown("### ① 基本資料")
        draft["name"] = st.text_input("中文名 *", value=draft["name"], key="reg_name")
        draft["name_en"] = st.text_input("英文名 *", value=draft["name_en"], key="reg_name_en")
        draft["birth_date"] = st.date_input(
            "出生年月日 *",
            value=draft["birth_date"],
            min_value=date(1950, 1, 1),
            max_value=date.today(),
            format="YYYY/MM/DD",
            key="reg_birth",
        )
        draft["gender"] = st.selectbox(
            "性別 *", GENDER_OPTIONS, index=GENDER_OPTIONS.index(draft["gender"]), key="reg_gender"
        )
        draft["hkaaa_id"] = st.text_input(
            "田總証編號 *", value=draft["hkaaa_id"], placeholder=HKAAA_ID_PLACEHOLDER, key="reg_hkaaa"
        )
        draft["hk_pr"] = st.selectbox(
            "香港永久性居民 *",
            HK_PERMANENT_OPTIONS,
            index=HK_PERMANENT_OPTIONS.index(draft["hk_pr"]),
            key="reg_hkpr",
        )
        if st.button("下一步 →", type="primary", use_container_width=True, key="reg_s1_next"):
            if not draft["name"].strip() or not draft["name_en"].strip():
                st.error("請填寫中文名及英文名")
            else:
                _set_register_step(2)
                st.rerun()

    elif step == 2:
        st.markdown("### ② 帳號與聯絡")
        draft["reg_user"] = st.text_input("登入帳號 *", value=draft["reg_user"], key="reg_user")
        draft["reg_pass"] = st.text_input("密碼 *", type="password", value=draft["reg_pass"], key="reg_pass")
        draft["phone"] = st.text_input("電話", value=draft["phone"], key="reg_phone")
        draft["school"] = st.text_input("學校", value=draft["school"], key="reg_school")
        draft["specialty"] = st.selectbox(
            "專項",
            SPECIALTY_OPTIONS,
            index=SPECIALTY_OPTIONS.index(draft["specialty"]),
            key="reg_spec",
        )
        draft["ec"] = st.text_input("緊急聯絡人", value=draft["ec"], key="reg_ec")
        draft["ep"] = st.text_input("緊急電話", value=draft["ep"], key="reg_ep")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 上一步", use_container_width=True, key="reg_s2_back"):
                _set_register_step(1)
                st.rerun()
        with c2:
            if st.button("下一步 →", type="primary", use_container_width=True, key="reg_s2_next"):
                if not draft["reg_user"].strip() or not draft["reg_pass"].strip():
                    st.error("請填寫登入帳號及密碼")
                else:
                    _set_register_step(3)
                    st.rerun()

    else:
        st.markdown("### ③ 健康申報與同意")
        with st.expander("📄 免責條款全文（必讀）", expanded=False):
            st.text(DISCLAIMER_FULL_TEXT)
        draft["health"] = st.text_area(
            "健康申報",
            value=draft["health"],
            height=80,
            placeholder=HEALTH_DECLARATION_PLACEHOLDER,
            key="reg_health",
        )
        agree = st.checkbox(AGREEMENT_LABEL, key="reg_agree")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 上一步", use_container_width=True, key="reg_s3_back"):
                _set_register_step(2)
                st.rerun()
        with c2:
            if st.button("提交註冊申請", type="primary", use_container_width=True, key="reg_submit"):
                if not agree:
                    st.error("請先閱讀免責條款並勾選同意聲明")
                elif not draft["reg_user"].strip() or not draft["name"].strip():
                    st.error("資料不完整，請返回上一步檢查")
                else:
                    register_user({
                        "username": draft["reg_user"].strip(),
                        "name": draft["name"].strip(),
                        "name_en": draft["name_en"].strip(),
                        **birth_fields_from_date(draft["birth_date"]),
                        "gender": draft["gender"],
                        "hkaaa_id": normalize_hkaaa_id(draft["hkaaa_id"]),
                        "hk_permanent_resident": draft["hk_pr"],
                        "school": draft["school"],
                        "specialty": draft["specialty"],
                        "phone": draft["phone"],
                        "password": draft["reg_pass"],
                        "emergency_contact": draft["ec"],
                        "emergency_phone": draft["ep"],
                        "health": draft["health"].strip() or "無",
                        "child_name": "",
                        "role": "pending",
                    })
                    st.session_state.register_success_info = {
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "username": draft["reg_user"].strip(),
                        "name": draft["name"].strip(),
                        "specialty": draft["specialty"],
                    }
                    st.session_state.register_submitted = True
                    st.rerun()

    if st.button("← 返回訪客專區", use_container_width=True, key="reg_back_visitor"):
        st.session_state.main_page = "訪客專區"
        st.rerun()
