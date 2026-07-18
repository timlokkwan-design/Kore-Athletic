"""Mobile UX helpers for coach program / calendar screens."""

from __future__ import annotations

import streamlit as st


def inject_coach_mobile_css() -> None:
    """Fix iOS scroll traps on coach program screens."""
    st.markdown(
        """
        <style>
        @media (max-width: 768px) {
            [data-testid="stAppViewContainer"],
            section.main,
            section.main .block-container {
                overflow-y: visible !important;
                -webkit-overflow-scrolling: touch !important;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-coach-screen-marker) [data-testid="stHorizontalBlock"] button {
                min-height: 2.85rem !important;
                font-weight: 700 !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_calendar_legend() -> None:
    st.markdown(
        """
        <div class="ka-cal-legend-marker"></div>
        <div class="ka-cal-legend">
            <span class="ka-leg-training">訓練</span>
            <span class="ka-leg-competition">比賽</span>
            <span class="ka-leg-rest">休息</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _set_coach_prog_screen(screen: str) -> None:
    st.session_state.coach_prog_screen = screen


def render_coach_screen_switcher(*, current: str) -> None:
    """Two big pills: pick date vs edit program (replaces tabs on mobile)."""
    inject_coach_mobile_css()
    st.markdown('<div class="ka-coach-screen-marker"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.button(
            "📅 選日期",
            key="coach_scr_cal",
            use_container_width=True,
            type="primary" if current == "cal" else "secondary",
            on_click=_set_coach_prog_screen,
            args=("cal",),
        )
    with c2:
        st.button(
            "✏️ 編輯課表",
            key="coach_scr_edit",
            use_container_width=True,
            type="primary" if current == "edit" else "secondary",
            on_click=_set_coach_prog_screen,
            args=("edit",),
        )
