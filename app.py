"""Track & field training management app — main entry point."""

import streamlit as st

from utils.data_store import init_sample_data
from views.coach_view import render_coach_view
from views.student_view import render_student_view

st.set_page_config(
    page_title="田徑隊訓練管理",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize sample CSV data on first run
if "initialized" not in st.session_state:
    init_sample_data()
    st.session_state.initialized = True


def main() -> None:
    with st.sidebar:
        st.header("🏃 田徑隊訓練管理")
        st.markdown("---")

        role = st.radio(
            "選擇身份",
            options=["學生端", "教練端"],
            index=0,
            help="學生端：記錄訓練數據 · 教練端：查看總覽與圖表",
        )

        st.markdown("---")
        st.caption("數據暫存於本地 CSV 檔案（`data/` 資料夾）")

    if role == "學生端":
        render_student_view()
    else:
        render_coach_view()


if __name__ == "__main__":
    main()
