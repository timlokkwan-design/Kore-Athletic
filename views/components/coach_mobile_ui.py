"""Mobile UX helpers for coach program / calendar screens."""

from __future__ import annotations

import streamlit as st


def inject_coach_mobile_css() -> None:
    """Fix iOS scroll traps and polish coach calendar on small screens."""
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
            div[data-testid="stVerticalBlock"]:has(.ka-cal-legend-marker) .ka-cal-legend {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin: 0.25rem 0 0.65rem;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-cal-legend-marker) .ka-cal-legend span {
                font-size: 0.72rem;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 999px;
                border: 1px solid transparent;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-cal-legend-marker) .ka-leg-training {
                background: #dbeafe;
                color: #1e40af;
                border-color: #93c5fd;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-cal-legend-marker) .ka-leg-competition {
                background: #fee2e2;
                color: #991b1b;
                border-color: #fca5a5;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-cal-legend-marker) .ka-leg-rest {
                background: #f1f5f9;
                color: #64748b;
                border-color: #e2e8f0;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-cal-list-row) [data-testid="stButton"] button {
                min-height: 3.1rem !important;
                text-align: left !important;
                justify-content: flex-start !important;
                padding: 0.65rem 0.85rem !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
            }
            div[data-testid="stVerticalBlock"]:has(.ka-cal-list-row) [data-testid="stCaptionContainer"] {
                margin-top: -0.35rem;
                padding-left: 0.15rem;
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
            <span class="ka-leg-training">🔵 訓練</span>
            <span class="ka-leg-competition">🔴 比賽</span>
            <span class="ka-leg-rest">⚪ 休息</span>
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
