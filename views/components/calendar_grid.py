"""Shared 7-column calendar week layout helpers (mobile-safe)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st

from views.components.stylable_shim import stylable_container

# Passed as separate blocks so stylable_container scopes every rule.
_WEEK_ROW_CSS_BLOCKS = [
    """
    div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
        gap: 3px !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    """,
    """
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"] > div {
        padding: 0 !important;
        margin: 0 !important;
        min-width: 0 !important;
        max-width: none !important;
        width: auto !important;
        flex: unset !important;
    }
    """,
]


def render_weekday_header_row(
    weekdays: list[str] | None = None,
    *,
    marker_class: str = "ka-tt-hdr",
) -> None:
    """Pure HTML weekday row — never uses st.columns (immune to mobile stack)."""
    labels = weekdays or ["日", "一", "二", "三", "四", "五", "六"]
    cells = "".join(
        f'<div class="{marker_class}"><p>{w}</p></div>' for w in labels
    )
    st.markdown(
        f'<div class="ka-cal-weekday-row" aria-hidden="true">{cells}</div>',
        unsafe_allow_html=True,
    )


@contextmanager
def calendar_week_row(*, key: str) -> Iterator[None]:
    """Wrap one st.columns(7) week so grid CSS is correctly scoped."""
    with stylable_container(key=key, css_styles=_WEEK_ROW_CSS_BLOCKS):
        st.markdown(
            '<div class="ka-cal-week-marker" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        yield
