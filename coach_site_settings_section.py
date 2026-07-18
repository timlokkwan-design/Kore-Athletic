"""Coach — edit public site content for visitor zone."""
from __future__ import annotations

import streamlit as st

from utils.backup import build_data_backup_zip
from utils.cloud_deploy import is_streamlit_cloud
from utils.site_content import DEFAULT_SITE_CONTENT, load_site_content, save_site_content


def render_coach_site_settings() -> None:
    st.subheader("網站內容設定")
    st.caption("以下內容顯示於「訪客專區」，不含學員個人資料。")

    content = load_site_content()

    with st.form("site_content_form"):
        club_intro = st.text_area("本會簡介", value=content.get("club_intro", ""), height=100)
        coach_intro = st.text_area("教練簡介", value=content.get("coach_intro", ""), height=100)
        contact_info = st.text_area("聯絡方式", value=content.get("contact_info", ""), height=80)
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
    st.markdown("##### 資料備份")
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
