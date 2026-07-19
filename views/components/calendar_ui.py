"""Calendar chrome using streamlit-extras (month nav, view toggle, shell)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st

from views.components.stylable_shim import stylable_container

from views.components.calendar_theme import get_calendar_palette, inject_calendar_theme


@contextmanager
def calendar_shell(*, key: str = "cal_shell") -> Iterator[None]:
    """Themed border wrapper around month grid / list."""
    inject_calendar_theme()
    p = get_calendar_palette()
    with stylable_container(
        key=key,
        css_styles=f"""
        {{
            background-color: {p['cell_bg']};
            border: 1px solid {p['list_card_border']};
            border-radius: 14px;
            padding: 0.65rem 0.55rem 0.75rem;
            margin: 0.25rem 0 0.5rem;
        }}
        """,
    ):
        st.markdown('<div class="ka-cal-shell-marker"></div>', unsafe_allow_html=True)
        yield


def render_calendar_month_nav(
    *,
    year: int,
    month: int,
    prev_key: str,
    next_key: str,
    on_prev,
    on_next,
    prev_args: tuple = (),
    next_args: tuple = (),
) -> None:
    """Month title + prev/next using streamlit-extras styled row."""
    inject_calendar_theme()
    with stylable_container(
        key=f"{prev_key}_nav_row",
        css_styles="""
        {
            background: transparent;
            border: none;
            padding: 0;
            margin-bottom: 0.35rem;
        }
        """,
    ):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            st.button("◀ 上月", key=prev_key, on_click=on_prev, args=prev_args, use_container_width=True)
        with c2:
            st.markdown(
                f'<h3 class="ka-cal-month-title">{year} 年 {month:02d} 月</h3>',
                unsafe_allow_html=True,
            )
        with c3:
            st.button("下月 ▶", key=next_key, on_click=on_next, args=next_args, use_container_width=True)


def render_calendar_view_toggle(
    key: str,
    *,
    current: str,
    on_select,
    force_grid: bool = False,
) -> str:
    """
    Grid / list toggle via streamlit-extras stylable_container + native buttons.
    Returns 'grid' or 'list'.
    """
    mode_key = f"{key}_view_mode"
    if force_grid:
        st.session_state[mode_key] = "grid"
        return "grid"

    if st.session_state.get(mode_key) not in ("grid", "list"):
        raw = st.session_state.get(mode_key)
        if isinstance(raw, str) and raw.startswith("📋"):
            st.session_state[mode_key] = "list"
        else:
            st.session_state[mode_key] = current if current in ("grid", "list") else "grid"

    mode = st.session_state[mode_key]
    inject_calendar_theme()
    p = get_calendar_palette()
    label_color = p["text_muted"]

    st.markdown(
        f'<p style="margin:0 0 0.25rem;font-size:0.78rem;font-weight:700;'
        f'color:{label_color};">檢視方式</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="ka-cal-view-marker"></div>', unsafe_allow_html=True)

    with stylable_container(
        key=f"{key}_view_toggle",
        css_styles=f"""
        {{
            background: {p['cell_empty_bg']};
            border: 1px solid {p['list_card_border']};
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 0.5rem;
        }}
        div[data-testid="stHorizontalBlock"] {{
            gap: 4px !important;
        }}
        button {{
            min-height: 2.65rem !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
        }}
        """,
    ):
        c1, c2 = st.columns(2)

        def _pick_grid():
            on_select(mode_key, "grid")

        def _pick_list():
            on_select(mode_key, "list")

        with c1:
            st.button(
                "📅 月曆",
                key=f"{key}_vm_grid",
                use_container_width=True,
                type="primary" if mode == "grid" else "secondary",
                on_click=_pick_grid,
            )
        with c2:
            st.button(
                "📋 列表",
                key=f"{key}_vm_list",
                use_container_width=True,
                type="primary" if mode == "list" else "secondary",
                on_click=_pick_list,
            )

    return st.session_state.get(mode_key, mode)


STUDENT_VIEW_MODES = ("list", "fullcalendar")


def render_student_schedule_view_toggle(
    key: str,
    *,
    default_mode: str = "fullcalendar",
) -> str:
    """Two-way toggle: FullCalendar / list. Returns mode string."""
    mode_key = f"{key}_view_mode"
    raw = st.session_state.get(mode_key)
    if raw not in STUDENT_VIEW_MODES:
        if raw == "grid":
            st.session_state[mode_key] = "fullcalendar"
        elif raw == "list" or (isinstance(raw, str) and raw.startswith("📋")):
            st.session_state[mode_key] = "list"
        else:
            st.session_state[mode_key] = default_mode if default_mode in STUDENT_VIEW_MODES else "fullcalendar"

    mode = st.session_state[mode_key]
    inject_calendar_theme()
    p = get_calendar_palette()
    label_color = p["text_muted"]

    st.markdown(
        f'<p style="margin:0 0 0.25rem;font-size:0.78rem;font-weight:700;'
        f'color:{label_color};">檢視方式</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="ka-cal-view-marker"></div>', unsafe_allow_html=True)

    with stylable_container(
        key=f"{key}_view_toggle2",
        css_styles=f"""
        {{
            background: {p['cell_empty_bg']};
            border: 1px solid {p['list_card_border']};
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 0.5rem;
        }}
        div[data-testid="stHorizontalBlock"] {{ gap: 4px !important; }}
        button {{
            min-height: 2.65rem !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            font-size: 0.82rem !important;
        }}
        """,
    ):
        c1, c2 = st.columns(2)

        def _pick(m: str):
            st.session_state[mode_key] = m

        with c1:
            st.button(
                "🗓 日曆",
                key=f"{key}_vm_fc",
                use_container_width=True,
                type="primary" if mode == "fullcalendar" else "secondary",
                on_click=_pick,
                args=("fullcalendar",),
            )
        with c2:
            st.button(
                "📋 列表",
                key=f"{key}_vm_list",
                use_container_width=True,
                type="primary" if mode == "list" else "secondary",
                on_click=_pick,
                args=("list",),
            )

    return st.session_state.get(mode_key, mode)


PROGRAM_VIEW_MODES = ("fullcalendar", "list")
SCHEDULE_VIEW_MODES = ("fullcalendar", "list")


def _render_multi_view_toggle(
    key: str,
    mode_key: str,
    modes: tuple[str, ...],
    labels: dict[str, str],
    default_mode: str,
) -> str:
    raw = st.session_state.get(mode_key)
    if raw not in modes:
        if raw == "grid" and "fullcalendar" in modes and "grid" not in modes:
            st.session_state[mode_key] = "fullcalendar"
        elif raw in modes:
            st.session_state[mode_key] = raw
        elif isinstance(raw, str) and raw.startswith("📋"):
            st.session_state[mode_key] = "list" if "list" in modes else default_mode
        else:
            st.session_state[mode_key] = default_mode if default_mode in modes else modes[0]

    mode = st.session_state[mode_key]
    inject_calendar_theme()
    p = get_calendar_palette()
    label_color = p["text_muted"]

    st.markdown(
        f'<p style="margin:0 0 0.25rem;font-size:0.78rem;font-weight:700;'
        f'color:{label_color};">檢視方式</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="ka-cal-view-marker"></div>', unsafe_allow_html=True)

    with stylable_container(
        key=f"{key}_view_toggle_multi",
        css_styles=f"""
        {{
            background: {p['cell_empty_bg']};
            border: 1px solid {p['list_card_border']};
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 0.5rem;
        }}
        div[data-testid="stHorizontalBlock"] {{ gap: 4px !important; }}
        button {{
            min-height: 2.65rem !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            font-size: 0.82rem !important;
        }}
        """,
    ):
        cols = st.columns(len(modes))

        def _pick(m: str):
            st.session_state[mode_key] = m

        for col, m in zip(cols, modes):
            with col:
                st.button(
                    labels.get(m, m),
                    key=f"{key}_vm_{m}",
                    use_container_width=True,
                    type="primary" if mode == m else "secondary",
                    on_click=_pick,
                    args=(m,),
                )

    return st.session_state.get(mode_key, mode)


def render_program_view_toggle(
    key: str,
    *,
    force_grid: bool = False,
    default_mode: str = "fullcalendar",
) -> str:
    """設定課表：日曆 / 列表（複製／刪除模式仍用方格月曆）。"""
    mode_key = f"{key}_view_mode"
    if force_grid:
        st.session_state[mode_key] = "grid"
        return "grid"
    return _render_multi_view_toggle(
        key,
        mode_key,
        PROGRAM_VIEW_MODES,
        {"fullcalendar": "🗓 日曆", "list": "📋 列表"},
        default_mode,
    )


def render_schedule_view_toggle(
    key: str,
    *,
    force_grid: bool = False,
    default_mode: str = "fullcalendar",
) -> str:
    """訓練時間表：日曆 / 列表（舊月曆自動改日曆）。"""
    mode_key = f"{key}_view_mode"
    if force_grid:
        st.session_state[mode_key] = "grid"
        return "grid"
    return _render_multi_view_toggle(
        key,
        mode_key,
        SCHEDULE_VIEW_MODES,
        {"fullcalendar": "🗓 日曆", "list": "📋 列表"},
        default_mode,
    )
