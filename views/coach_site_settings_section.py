"""Coach — edit public site content for visitor zone."""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from utils.backup import build_data_backup_zip
from utils.cloud_deploy import is_streamlit_cloud
from utils.data_store import USER_COLUMNS, load_users
from utils.site_content import DEFAULT_SITE_CONTENT, load_site_content, save_site_content
from utils.user_protection import (
    build_users_only_backup,
    count_protected,
    load_users_backup_payload,
    restore_users_from_backup,
    snapshot_users_backup,
)


def _render_user_account_protection() -> None:
    st.markdown("##### 學員帳號保護（獨立）")
    st.caption(
        "更新程式／重新部署時，系統會自動合併現有帳號，避免學生用戶消失。"
        "你亦可單獨下載／還原「用戶帳號」備份。"
    )

    users = load_users()
    protected = count_protected(users)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("受保護帳號", protected["total"])
    c2.metric("學員", protected["student"])
    c3.metric("待審", protected["pending"])
    c4.metric("家長", protected["parent"])

    payload = load_users_backup_payload()
    if payload:
        st.success(
            f"最近自動備份：{payload.get('saved_at', '—')} · "
            f"{payload.get('count', 0)} 個帳號"
        )
    else:
        st.warning("尚未有用戶帳號自動備份。按下方按鈕可立即建立。")

    if st.button("立即備份用戶帳號", key="users_backup_now", use_container_width=True):
        info = snapshot_users_backup(users, USER_COLUMNS, reason="manual-coach")
        st.success(f"已備份 {info['count']} 個帳號")
        st.rerun()

    users_csv, users_name = build_users_only_backup()
    st.download_button(
        "只下載用戶帳號（CSV）",
        data=users_csv,
        file_name=users_name,
        mime="text/csv",
        use_container_width=True,
        key="coach_users_only_backup",
    )

    uploaded = st.file_uploader(
        "還原用戶帳號（上傳 users CSV）",
        type=["csv"],
        key="coach_users_restore_upload",
        help="會與現有帳號合併，不會刪除已存在的其他學生。",
    )
    if uploaded is not None and st.button(
        "從上傳檔合併還原",
        key="coach_users_restore_btn",
        type="primary",
        use_container_width=True,
    ):
        try:
            df = pd.read_csv(io.BytesIO(uploaded.getvalue()))
            result = restore_users_from_backup(uploaded_df=df)
            st.success(
                f"已合併還原 {result['restored_rows']} 列；"
                f"現共 {result['total_after']} 帳號"
                f"（受保護 {result['protected_after']['total']}）"
            )
            st.rerun()
        except Exception as exc:
            st.error(f"還原失敗：{exc}")

    if payload and st.button(
        "從最近自動備份合併還原",
        key="coach_users_restore_auto",
        use_container_width=True,
    ):
        try:
            result = restore_users_from_backup(payload=payload)
            st.success(
                f"已合併還原；現共 {result['total_after']} 帳號"
                f"（受保護 {result['protected_after']['total']}）"
            )
            st.rerun()
        except Exception as exc:
            st.error(f"還原失敗：{exc}")


def render_coach_site_settings() -> None:
    st.subheader("網站內容設定")
    st.caption("以下內容顯示於「訪客專區」，不含學員個人資料。")

    content = load_site_content()

    with st.form("site_content_form"):
        club_intro = st.text_area("本會簡介", value=content.get("club_intro", ""), height=100)
        coach_intro = st.text_area("教練簡介", value=content.get("coach_intro", ""), height=100)
        contact_info = st.text_area("聯絡方式（公開顯示）", value=content.get("contact_info", ""), height=80)
        instagram_handle = st.text_input(
            "Instagram 帳號（公開）",
            value=content.get("instagram_handle", ""),
            placeholder="koreathletic_kwansir",
            help="訪客／學員可見，用於查詢及忘記密碼等，不含電話。",
        )
        st.markdown("**教練專用（不公開）**")
        coach_whatsapp = st.text_input(
            "教練 WhatsApp（僅後台使用）",
            value=content.get("coach_whatsapp", ""),
            placeholder="85291234567",
            help="不會顯示給訪客。填寫後，核准學員時可一鍵開 WhatsApp **通知該學員**（連結指向學員電話，不暴露教練號碼）。",
        )
        join_process = st.text_area("如何加入（步驟）", value=content.get("join_process", ""), height=100)

        st.markdown("**公開設定**")
        public_pb = st.checkbox(
            "允許訪客查看 PB 排行榜（只顯示項目及成績，不顯示姓名）",
            value=bool(content.get("public_pb_leaderboard")),
        )

        if st.form_submit_button("儲存網站內容", type="primary", use_container_width=True):
            save_site_content({
                "club_intro": club_intro,
                "coach_intro": coach_intro,
                "contact_info": contact_info,
                "instagram_handle": instagram_handle,
                "coach_whatsapp": coach_whatsapp,
                "join_process": join_process,
                "public_pb_leaderboard": public_pb,
            })
            st.success("已更新訪客專區內容")
            st.rerun()

    with st.expander("恢復預設文案"):
        st.caption("將覆寫為系統預設文字（保留目前 PB 公開設定）。")
        if st.button("恢復預設", key="site_content_reset"):
            save_site_content({
                **DEFAULT_SITE_CONTENT,
                "public_pb_leaderboard": content.get("public_pb_leaderboard"),
            })
            st.success("已恢復預設文案")
            st.rerun()

    st.markdown("---")
    _render_user_account_protection()

    st.markdown("---")
    st.markdown("##### 完整資料備份")
    st.caption(
        "雲端上線後，學員資料存於伺服器。請定期下載備份；"
        "更新 GitHub 程式碼重新部署前，務必先備份。"
    )
    backup_bytes, backup_name = build_data_backup_zip()
    st.download_button(
        "下載 data 資料備份（ZIP）",
        data=backup_bytes,
        file_name=backup_name,
        mime="application/zip",
        use_container_width=True,
        key="coach_data_backup",
    )

    if is_streamlit_cloud():
        st.info(
            "目前運行於 **Streamlit 免費雲端**。網址可分享給學生；"
            "教練密碼在 share.streamlit.io → Settings → Secrets 設定。"
        )
    from utils.supabase_config import is_supabase_enabled

    if is_supabase_enabled():
        st.success("資料庫：**Supabase 雲端**（已啟用）")
    else:
        from utils.supabase_config import get_supabase_credentials

        url, key = get_supabase_credentials()
        if url and not key:
            st.warning("已設定 Supabase URL，但 **service_key 仍为空**。请双击 **`設定Supabase密钥.bat`** 写入密钥。")
        else:
            st.caption("資料庫：本機 CSV（可在 Secrets 設定 Supabase 以改用雲端資料庫）")
