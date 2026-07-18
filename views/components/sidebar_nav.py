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


def _set_main_page(session_key: str, page: str) -> None:
    st.session_state[session_key] = page


def render_main_top_nav(
    options: list[tuple[str, str]],
    session_key: str,
    default: str,
) -> str:
    """Compact main-area nav: first item upper-left, others upper-right."""
    values = [val for _, val in options]
    if session_key not in st.session_state or st.session_state[session_key] not in values:
        st.session_state[session_key] = default

    current = st.session_state[session_key]
    if not options:
        return current

    left_label, left_val = options[0]
    right_opts = options[1:]

    st.markdown('<div class="ka-main-nav-wrap">', unsafe_allow_html=True)
    left_col, _, right_col = st.columns([1.1, 2.8, 1.1])

    with left_col:
        st.button(
            left_label,
            key=f"main_hdr_{left_val}",
            use_container_width=True,
            type="primary" if current == left_val else "secondary",
            on_click=_set_main_page,
            args=(session_key, left_val),
        )

    if right_opts:
        with right_col:
            rcols = st.columns(len(right_opts))
            for col, (label, val) in zip(rcols, right_opts):
                with col:
                    st.button(
                        label,
                        key=f"main_hdr_{val}",
                        use_container_width=True,
                        type="primary" if current == val else "secondary",
                        on_click=_set_main_page,
                        args=(session_key, val),
                    )

    st.markdown("</div>", unsafe_allow_html=True)
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
