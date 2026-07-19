"""Mobile UX helpers for coach program / calendar screens."""

from __future__ import annotations

import streamlit as st

from views.components.stylable_shim import stylable_container

from views.components.calendar_theme import get_calendar_palette, inject_calendar_theme


def inject_coach_mobile_css() -> None:
    """Fix iOS scroll traps on coach program screens."""
    st.markdown(
        """
        <style>
        /* Force paired action buttons to stay on one row on mobile */
        [data-testid="stVerticalBlock"]:has(.ka-force-row) > [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.35rem !important;
            width: 100% !important;
        }
        [data-testid="stVerticalBlock"]:has(.ka-force-row) > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 0 !important;
            flex: 1 1 0 !important;
        }
        [data-testid="stVerticalBlock"]:has(.ka-force-row) button {
            white-space: nowrap !important;
            font-size: clamp(0.62rem, 2.7vw, 0.88rem) !important;
            min-height: 2.5rem !important;
            font-weight: 700 !important;
            padding-left: 0.15rem !important;
            padding-right: 0.15rem !important;
        }
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


def mark_force_row() -> None:
    """Place before st.columns(...) so the row stays horizontal on phones."""
    st.markdown(
        '<div class="ka-force-row ka-inline-row-marker"></div>',
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
    inject_calendar_theme()
    p = get_calendar_palette()
    st.markdown(
        '<div class="ka-coach-screen-marker ka-inline-row-marker"></div>',
        unsafe_allow_html=True,
    )
    with stylable_container(
        key="coach_scr_switch",
        css_styles=f"""
        {{
            background: {p['cell_empty_bg']};
            border: 1px solid {p['list_card_border']};
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 0.5rem;
        }}
        button {{ min-height: 2.75rem !important; font-weight: 700 !important; border-radius: 8px !important; }}
        """,
    ):
        st.markdown(
            '<div class="ka-inline-row-marker"></div>',
            unsafe_allow_html=True,
        )
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
