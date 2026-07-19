"""Mobile UX helpers for coach program / calendar screens."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st

from views.components.stylable_shim import stylable_container

from views.components.calendar_theme import get_calendar_palette, inject_calendar_theme


def inject_coach_mobile_css() -> None:
    """Fix iOS scroll traps on coach program screens."""
    st.markdown(
        """
        <style>
        @media (max-width: 768px) {
            html, body, .stApp,
            [data-testid="stAppViewContainer"],
            section.main,
            section.main .block-container {
                overflow-x: hidden !important;
                overflow-y: auto !important;
                max-width: 100% !important;
                -webkit-overflow-scrolling: touch !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mark_force_row() -> None:
    """Deprecated: prefer force_button_row(). Kept for rare non-button column rows."""
    st.markdown(
        '<div class="ka-force-row" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


@contextmanager
def force_button_row(
    *,
    key: str,
    n_cols: int = 2,
    weights: list[float] | None = None,
    marker_extra: str = "",
) -> Iterator[list]:
    """Reliable one-row chip/button strip (stylable_container + scoped CSS).

    Prefer this for 2–5 action chips on mobile. Yields ``st.columns(...)``.
    Optional ``weights`` (same length as n_cols) for unequal flex, e.g. month nav.
    """
    inject_coach_mobile_css()
    inject_calendar_theme()
    p = get_calendar_palette()
    if weights is not None and len(weights) != n_cols:
        weights = None
    marker_cls = "ka-force-row-host ka-inline-row-marker"
    if n_cols > 5:
        marker_cls = "ka-force-row-host"
    if marker_extra:
        marker_cls = f"{marker_cls} {marker_extra}".strip()

    if weights:
        flex_rules = "\n".join(
            f"""
            div[data-testid="stHorizontalBlock"] > div:nth-child({i + 1}) {{
                flex: {w} 1 0 !important;
                min-width: 0 !important;
                max-width: none !important;
                width: auto !important;
            }}
            """
            for i, w in enumerate(weights)
        )
        col_spec: int | list[float] = list(weights)
    else:
        flex_rules = """
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 0 !important;
            max-width: none !important;
            width: auto !important;
            flex: 1 1 0 !important;
        }
        """
        col_spec = n_cols

    with stylable_container(
        key=key,
        css_styles=[
            f"""
            {{
                background: {p['cell_empty_bg']};
                border: 1px solid {p['list_card_border']};
                border-radius: 12px;
                padding: 4px;
                margin: 0.15rem 0 0.45rem;
            }}
            """,
            """
            div[data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                gap: 4px !important;
                width: 100% !important;
                max-width: 100% !important;
            }
            """,
            flex_rules,
            """
            button {
                min-height: 2.55rem !important;
                font-weight: 700 !important;
                border-radius: 8px !important;
                font-size: clamp(0.62rem, 2.6vw, 0.85rem) !important;
                padding-left: 0.1rem !important;
                padding-right: 0.1rem !important;
                white-space: nowrap !important;
            }
            """,
        ],
    ):
        st.markdown(
            f'<div class="{marker_cls}" data-ka-cols="{n_cols}" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        yield st.columns(col_spec, gap="small")


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
    with force_button_row(
        key="coach_scr_switch",
        n_cols=2,
        marker_extra="ka-coach-screen-marker",
    ) as cols:
        c1, c2 = cols
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
