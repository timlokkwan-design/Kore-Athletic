"""Categorized sidebar navigation."""
from __future__ import annotations

import streamlit as st


def _select_nav_section(session_key: str, item: str) -> None:
    st.session_state[session_key] = item


def render_nav_categories(
    categories: list[tuple[str, list[str]]],
    session_key: str,
    default: str,
    badges: dict[str, int] | None = None,
) -> str:
    if session_key not in st.session_state:
        st.session_state[session_key] = default

    selected = st.session_state[session_key]
    all_items = [item for _, items in categories for item in items]
    if selected not in all_items:
        st.session_state[session_key] = default
        selected = default

    st.markdown(
        "<p class='ka-nav-label'>功能分頁</p>",
        unsafe_allow_html=True,
    )
    for cat_label, items in categories:
        expanded = selected in items
        with st.expander(cat_label, expanded=expanded):
            for item in items:
                is_active = item == selected
                badge = (badges or {}).get(item, 0)
                label = f"{item} ({badge})" if badge > 0 else item
                st.button(
                    label,
                    key=f"{session_key}_{item}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_select_nav_section,
                    args=(session_key, item),
                )

    return st.session_state[session_key]


def render_top_nav(
    options: list[tuple[str, str]],
    session_key: str,
    default: str,
) -> str:
    """Render top-level pages; options = [(label, value), ...]."""
    labels = [label for label, _ in options]
    label_to_value = dict(options)
    values = list(label_to_value.values())

    if session_key not in st.session_state or st.session_state[session_key] not in values:
        st.session_state[session_key] = default

    current = st.session_state[session_key]
    current_label = next((lbl for lbl, val in options if val == current), labels[0])
    picked_label = st.radio(
        "主選單",
        labels,
        index=labels.index(current_label),
        label_visibility="collapsed",
    )
    st.session_state[session_key] = label_to_value[picked_label]
    return st.session_state[session_key]
