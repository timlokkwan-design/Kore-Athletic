"""Mobile-first navigation — Instagram-style bottom tab bars."""
from __future__ import annotations

import time

import streamlit as st


def _set_main_page(session_key: str, page: str) -> None:
    st.session_state[session_key] = page


def _set_section_with_feedback(session_key: str, section: str) -> None:
    """Switch section and mark a press flash so the tile reacts on the next paint."""
    st.session_state[session_key] = section
    st.session_state["_bottom_tab_flash"] = section
    st.session_state["_bottom_tab_flash_at"] = time.time()


def render_visitor_sidebar_nav(
    options: list[tuple[str, str]],
    session_key: str,
    default: str,
) -> str:
    """Visitor navigation inside sidebar (replaces main-area top buttons)."""
    values = [val for _, val in options]
    if session_key not in st.session_state or st.session_state[session_key] not in values:
        st.session_state[session_key] = default

    st.markdown("<p class='ka-nav-label'>瀏覽</p>", unsafe_allow_html=True)
    current = st.session_state[session_key]
    for label, val in options:
        st.button(
            label,
            key=f"vis_nav_{val}",
            use_container_width=True,
            type="primary" if current == val else "secondary",
            on_click=_set_main_page,
            args=(session_key, val),
        )
    return st.session_state[session_key]


def _render_bottom_tabbar(
    *,
    marker_class: str,
    items: list[tuple[str, str, str]],
    current_section: str,
    session_key: str,
    key_prefix: str,
    active_aliases: dict[str, set[str]] | None = None,
) -> None:
    """Fixed bottom tab bar — single horizontal row on mobile (Instagram-style).

    items: (icon, short_label, section_value)
    active_aliases: map dock section → other sections that should also light up the tile
    """
    # Reinforce layout every render (Streamlit mobile CSS can wrap columns).
    # Applies to BOTH student (.ka-student-dock-marker) and coach (.ka-coach-dock-marker).
    st.markdown(
        """
        <style>
        @media (max-width: 768px) {
          div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlock"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlock"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            gap: 0.18rem !important;
          }
          div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlock"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlock"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) [data-testid="column"],
          div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) [data-testid="stColumn"],
          div[data-testid="stVerticalBlock"]:has(.ka-student-dock-marker) [data-testid="column"],
          div[data-testid="stVerticalBlock"]:has(.ka-student-dock-marker) [data-testid="stColumn"],
          div[data-testid="stVerticalBlock"]:has(.ka-coach-dock-marker) [data-testid="column"],
          div[data-testid="stVerticalBlock"]:has(.ka-coach-dock-marker) [data-testid="stColumn"] {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            width: auto !important;
            max-width: none !important;
          }
        }
        @media (min-width: 769px) {
          div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlock"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlock"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"],
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
          }
          div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlock"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlock"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-bottom-tabbar-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-student-dock-marker) [data-testid="stHorizontalBlock"] > div,
          div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-coach-dock-marker) [data-testid="stHorizontalBlock"] > div {
            flex: 1 1 0 !important;
            min-width: 0 !important;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    flash = st.session_state.get("_bottom_tab_flash")
    if flash:
        st.markdown(
            """
            <style>
            @keyframes ka-tab-pop {
              0%   { transform: scale(0.86); filter: brightness(1.15); }
              55%  { transform: scale(1.06); }
              100% { transform: scale(1); }
            }
            div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) button[kind="primary"],
            div[data-testid="stVerticalBlock"]:has(.ka-bottom-tabbar-marker) button[data-testid="baseButton-primary"],
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-bottom-tabbar-marker) button[kind="primary"],
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.ka-bottom-tabbar-marker) button[data-testid="baseButton-primary"] {
              animation: ka-tab-pop 0.3s ease !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    with st.container():
        st.markdown(f'<div class="{marker_class}" aria-hidden="true"></div>', unsafe_allow_html=True)
        cols = st.columns(len(items), gap="small")
        aliases = active_aliases or {}
        for col, (icon, label, section) in zip(cols, items):
            related = aliases.get(section, set())
            is_active = current_section == section or current_section in related
            btn_label = f"{icon}\n{label}"
            with col:
                st.button(
                    btn_label,
                    key=f"{key_prefix}_{section}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_set_section_with_feedback,
                    args=(session_key, section),
                )

    if flash is not None:
        st.session_state.pop("_bottom_tab_flash", None)


def render_student_quick_dock(current_section: str) -> None:
    """Student Instagram-style bottom tabs: 課表 / 簽到 / 日誌 / 比賽."""
    _render_bottom_tabbar(
        marker_class="ka-bottom-tabbar-marker ka-student-dock-marker",
        items=[
            ("📅", "課表", "訓練時間表"),
            ("✅", "簽到", "出席"),
            ("📝", "日誌", "訓練日誌"),
            ("🏅", "比賽", "比賽報名"),
        ],
        current_section=current_section,
        session_key="student_section",
        key_prefix="stu_dock",
        active_aliases={"比賽報名": {"賽事時間表", "提交比賽成績"}},
    )


def render_coach_bottom_dock(current_section: str) -> None:
    """Coach Instagram-style bottom tabs: 總覽 / 課表 / 出席 / 隊伍 / 比賽."""
    _render_bottom_tabbar(
        marker_class="ka-bottom-tabbar-marker ka-coach-dock-marker",
        items=[
            ("🏠", "總覽", "總覽"),
            ("📅", "課表", "訓練時間表"),
            ("✅", "出席", "出席表"),
            ("👥", "隊伍", "隊伍管理"),
            ("🏅", "比賽", "比賽報名表"),
        ],
        current_section=current_section,
        session_key="coach_section",
        key_prefix="coach_dock",
        active_aliases={"比賽報名表": {"賽事時間表", "比賽管理"}, "訓練時間表": {"設定課表"}},
    )
