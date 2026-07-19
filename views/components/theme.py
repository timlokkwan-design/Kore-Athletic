"""Global UI theme, CSS, and shared layout components."""
from __future__ import annotations

import streamlit as st

# Light theme tokens
LIGHT = {
    "text": "#0f172a",
    "muted": "#64748b",
    "border": "#e2e8f0",
    "card_bg": "#f8fafc",
    "main_bg": "#ffffff",
    "primary": "#64748b",
}
# Dark main-content tokens (sidebar stays dark via config.toml)
DARK = {
    "text": "#e2e8f0",
    "muted": "#94a3b8",
    "border": "#334155",
    "card_bg": "#1a1d24",
    "main_bg": "#0f1117",
    "primary": "#94a3b8",
}

COLOR_SUCCESS_BG = "#dcfce7"
COLOR_SUCCESS_BORDER = "#86efac"
COLOR_WARN_BG = "#fef3c7"
COLOR_WARN_BORDER = "#fcd34d"
COLOR_DANGER_BG = "#fee2e2"
COLOR_DANGER_BORDER = "#fca5a5"
RADIUS = "10px"


def get_ui_theme() -> str:
    return st.session_state.get("ui_theme", "light")


def get_ui_colors() -> dict[str, str]:
    """Current main-content theme tokens for inline HTML."""
    return dict(DARK if get_ui_theme() == "dark" else LIGHT)


def _set_ui_theme(theme: str) -> None:
    theme = "dark" if theme == "dark" else "light"
    st.session_state.ui_theme = theme
    st.session_state.ui_theme_toggle = theme == "dark"


def render_theme_toggle() -> None:
    """Sidebar theme switch (kept for discoverability when menu is open)."""
    st.toggle(
        "夜光模式（主內容區）",
        value=get_ui_theme() == "dark",
        key="ui_theme_toggle",
        help="開啟＝夜光／關閉＝日光（側欄維持深色）",
        on_change=_sync_theme_from_toggle,
    )


def _sync_theme_from_toggle() -> None:
    st.session_state.ui_theme = "dark" if st.session_state.get("ui_theme_toggle") else "light"


def render_theme_toggle_top() -> None:
    """Fixed top-right 日光 / 夜光 controls — visible without opening the sidebar."""
    dark = get_ui_theme() == "dark"

    with st.container():
        st.markdown('<div class="ka-theme-top-marker"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button(
                "☀️ 日光",
                key="ka_theme_light_btn",
                use_container_width=True,
                type="primary" if not dark else "secondary",
                help="日光模式",
            ):
                _set_ui_theme("light")
                st.rerun()
        with c2:
            if st.button(
                "🌙 夜光",
                key="ka_theme_dark_btn",
                use_container_width=True,
                type="primary" if dark else "secondary",
                help="夜光模式",
            ):
                _set_ui_theme("dark")
                st.rerun()

    # Pin after marker exists in DOM (also re-pins dock/subtabs when present)
    try:
        from views.components.mobile_nav import _pin_innermost_dock_host

        _pin_innermost_dock_host()
    except Exception:
        pass



def inject_global_css(theme: str | None = None, role_class: str = "", **_kwargs) -> None:
    """Inject global CSS. role_class is optional (legacy callers may omit it)."""
    t = theme or get_ui_theme()
    c = DARK if t == "dark" else LIGHT
    role_attr = f"ka-role-{role_class}" if role_class else ""

    if t == "dark":
        bar_success_style = "background:#14532d;border:1px solid #22c55e;color:#bbf7d0;"
        bar_warn_style = "background:#422006;border:1px solid #f59e0b;color:#fde68a;"
        pwa_hint_style = "background:#1e3a5f;border:1px solid #3b82f6;color:#bfdbfe;"
        pwa_detail_style = "color:#94a3b8;"
        sidebar_pending_style = "background:#422006;border:1px solid #f59e0b;color:#fde68a;"
    else:
        bar_success_style = f"background:{COLOR_SUCCESS_BG};border:1px solid {COLOR_SUCCESS_BORDER};color:#166534;"
        bar_warn_style = f"background:{COLOR_WARN_BG};border:1px solid {COLOR_WARN_BORDER};color:#92400e;"
        pwa_hint_style = "background:#eff6ff;border:1px solid #93c5fd;color:#1e3a8a;"
        pwa_detail_style = "color:#475569;"
        sidebar_pending_style = f"background:{COLOR_WARN_BG};border:1px solid {COLOR_WARN_BORDER};color:#92400e;"

    dark_stat_override = ""
    if t == "dark":
        dark_stat_override = """
        .ka-stat-card { background: #1a1d24 !important; border-color: #334155 !important; }
        .ka-stat-value { color: #e2e8f0 !important; }
        .ka-lb-card { background: #1a1d24 !important; border-color: #334155 !important; color: #e2e8f0; }
        .ka-empty { background: #1a1d24 !important; border-color: #334155 !important; }
        """

    st.markdown(
        f"""
        <style>
        section.main .block-container {{
            background-color: {c["main_bg"]};
            padding-top: 0.65rem;
        }}
        section.main {{
            background-color: {c["main_bg"]};
        }}
        /* Hide deploy/status chrome only — keep header sidebar expand controls */
        .stDeployButton,
        [data-testid="stAppDeployButton"],
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] {{
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }}
        /* Do not hide stToolbar / stHeaderActionElements — that removes sidebar open */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        /* Sidebar expand control — always visible & large enough to tap */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stExpandSidebarButton"] {{
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            z-index: 2147483646 !important;
        }}
        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button,
        [data-testid="stSidebarCollapseButton"] button {{
            min-width: 2.75rem !important;
            min-height: 2.75rem !important;
        }}
        hr {{ margin: 0.75rem 0; border-color: {c["border"]}; }}
        section.main [data-testid="stMarkdownContainer"] h1,
        section.main [data-testid="stMarkdownContainer"] h2,
        section.main [data-testid="stMarkdownContainer"] h3,
        section.main [data-testid="stMarkdownContainer"] h4,
        section.main [data-testid="stMarkdownContainer"] h5,
        section.main [data-testid="stMarkdownContainer"] h6 {{
            color: {c["text"]} !important;
        }}
        section.main [data-testid="stMarkdownContainer"] p,
        section.main [data-testid="stMarkdownContainer"] li,
        section.main [data-testid="stMarkdownContainer"] span {{
            color: {c["text"]};
        }}
        section.main [data-testid="stCaptionContainer"],
        section.main [data-testid="stCaptionContainer"] p,
        section.main [data-testid="stCaptionContainer"] small {{
            color: {c["muted"]} !important;
        }}
        section.main label[data-testid="stWidgetLabel"] p,
        section.main label[data-testid="stWidgetLabel"] span,
        section.main .stSelectbox label p,
        section.main .stTextInput label p,
        section.main .stTextArea label p {{
            color: {c["text"]} !important;
        }}
        section.main [data-testid="stAlert"] p,
        section.main [data-testid="stAlert"] {{
            color: {c["text"]};
        }}
        section.main [data-testid="stExpander"] summary,
        section.main [data-testid="stExpander"] summary p {{
            color: {c["text"]} !important;
        }}
        section.main [data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p {{
            color: {c["text"]};
        }}
        .ka-nav-label {{
            margin: 14px 0 6px;
            font-size: 11px;
            font-weight: 700;
            color: {c["muted"]};
            letter-spacing: 0.04em;
        }}
        .ka-main-nav-wrap {{
            margin: 0 0 0.65rem 0;
            padding: 0;
        }}
        .ka-main-nav-wrap [data-testid="column"] {{
            padding-left: 0.2rem !important;
            padding-right: 0.2rem !important;
        }}
        .ka-main-nav-wrap [data-testid="column"] button {{
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            min-height: 2rem !important;
            max-height: 2.15rem !important;
            padding: 0.2rem 0.45rem !important;
            white-space: nowrap;
        }}
        @media (max-width: 768px) {{
            .ka-main-nav-wrap [data-testid="column"] button {{
                font-size: 0.76rem !important;
                padding: 0.15rem 0.3rem !important;
            }}
        }}
        .ka-breadcrumb {{
            font-size: 0.82rem;
            color: {c["muted"]};
            margin-bottom: 0.35rem;
        }}
        .ka-breadcrumb b {{ color: {c["text"]}; font-weight: 600; }}
        .ka-page-title {{
            margin: 0;
            font-size: 1.55rem;
            font-weight: 800;
            color: {c["text"]};
            letter-spacing: -0.01em;
        }}
        .ka-page-sub {{
            margin: 0.2rem 0 0;
            font-size: 0.88rem;
            color: {c["muted"]};
        }}
        .ka-stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        .ka-stat-grid.ka-stat-grid-3 {{
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.45rem;
        }}
        .ka-stat-card {{
            background: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS};
            padding: 0.85rem 1rem;
        }}
        .ka-stat-grid-3 .ka-stat-card {{
            padding: 0.65rem 0.45rem;
            text-align: center;
        }}
        .ka-stat-label {{
            font-size: 0.75rem;
            color: {c["muted"]};
            margin-bottom: 0.25rem;
        }}
        .ka-stat-grid-3 .ka-stat-label {{
            font-size: 0.68rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .ka-stat-value {{
            font-size: 1.35rem;
            font-weight: 800;
            color: {c["text"]};
            line-height: 1.2;
        }}
        .ka-stat-grid-3 .ka-stat-value {{
            font-size: 1.05rem;
        }}
        /* Student goals — cleaner card look */
        .ka-goal-wrap {{
            background: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS};
            padding: 0.85rem 0.9rem;
            margin: 0 0 1rem 0;
        }}
        .ka-goal-title {{
            margin: 0 0 0.55rem 0;
            font-size: 1.05rem;
            font-weight: 800;
            color: {c["text"]};
        }}
        .ka-goal-card {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.65rem;
            background: {c["main_bg"]};
            border: 1px solid {c["border"]};
            border-radius: 10px;
            padding: 0.7rem 0.75rem;
            margin-bottom: 0.5rem;
        }}
        .ka-goal-event {{
            font-weight: 800;
            color: {c["text"]};
            font-size: 0.95rem;
        }}
        .ka-goal-meta {{
            margin-top: 0.2rem;
            font-size: 0.8rem;
            color: {c["muted"]};
            line-height: 1.35;
        }}
        .ka-goal-empty {{
            font-size: 0.85rem;
            color: {c["muted"]};
            margin: 0 0 0.45rem 0;
        }}
        .ka-sidebar-open-btn {{
            /* ensure menu stays above docks but sidebar can cover content */
        }}
        section[data-testid="stSidebar"] {{
            z-index: 2147483645 !important;
        }}
        section[data-testid="stSidebar"] > div {{
            background-color: #0e1117 !important;
            opacity: 1 !important;
        }}
        /* Top subtabs sit under sidebar when drawer is open */
        .ka-top-subtab-host {{
            z-index: 2147482800 !important;
        }}
        .ka-bottom-dock-host {{
            z-index: 2147483000 !important;
        }}
        .ka-bar {{
            border-radius: {RADIUS};
            padding: 0.55rem 0.85rem;
            font-size: 0.88rem;
            margin-bottom: 0.75rem;
        }}
        .ka-bar-success {{
            {bar_success_style}
        }}
        .ka-bar-warn {{
            {bar_warn_style}
        }}
        .ka-lb-card {{
            background: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS};
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            color: {c["text"]};
        }}
        .ka-lb-rank {{
            font-size: 1.1rem;
            font-weight: 800;
            color: {c["primary"]};
            min-width: 2rem;
        }}
        .ka-lb-top1 {{ border-left: 4px solid #eab308; }}
        .ka-lb-top2 {{ border-left: 4px solid #94a3b8; }}
        .ka-lb-top3 {{ border-left: 4px solid #b45309; }}
        .ka-empty {{
            background: {c["card_bg"]};
            border: 1px dashed {c["border"]};
            border-radius: {RADIUS};
            padding: 1.25rem;
            text-align: center;
            margin: 0.5rem 0 1rem;
        }}
        .ka-empty-title {{
            font-weight: 700;
            color: {c["text"]};
            margin-bottom: 0.35rem;
        }}
        .ka-empty-hint {{
            font-size: 0.85rem;
            color: {c["muted"]};
        }}
        .ka-sidebar-pending {{
            {sidebar_pending_style}
            border-radius: {RADIUS};
            padding: 0.65rem 0.75rem;
            margin-bottom: 0.35rem;
        }}
        .ka-sidebar-pending-title {{
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
        }}
        .ka-sidebar-pending-badge {{
            background: #f59e0b;
            color: #fff;
            font-size: 0.72rem;
            font-weight: 800;
            min-width: 1.35rem;
            height: 1.35rem;
            line-height: 1.35rem;
            text-align: center;
            border-radius: 999px;
            padding: 0 0.35rem;
        }}
        .ka-sidebar-pending-list {{
            margin: 0;
            padding: 0;
            list-style: none;
            font-size: 0.78rem;
        }}
        .ka-sidebar-pending-list li {{
            display: flex;
            justify-content: space-between;
            gap: 0.5rem;
            padding: 0.12rem 0;
        }}
        .ka-sidebar-pending-list strong {{
            font-weight: 800;
        }}
        .ka-pending-mobile-banner {{
            {sidebar_pending_style}
            border-radius: {RADIUS};
            padding: 0.75rem 0.85rem;
            margin: 0 0 0.65rem 0;
        }}
        .ka-pending-mobile-banner-title {{
            font-size: 0.95rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }}
        .ka-pending-mobile-banner-detail {{
            font-size: 0.82rem;
            opacity: 0.95;
        }}
        {dark_stat_override}
        @media (max-width: 768px) {{
            .ka-stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .ka-stat-grid.ka-stat-grid-3 {{
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
                gap: 0.4rem !important;
            }}
            .ka-stat-grid-3 .ka-stat-value {{ font-size: 0.98rem !important; }}
            .ka-stat-grid-3 .ka-stat-label {{ font-size: 0.62rem !important; }}
            section.main .block-container {{
                padding-left: 0.65rem;
                padding-right: 0.65rem;
                max-width: 100% !important;
            }}
            .ka-page-title {{ font-size: 1.25rem !important; }}
            .ka-pending-mobile-banner {{
                position: sticky;
                top: 0;
                z-index: 20;
                box-shadow: 0 4px 14px rgba(0,0,0,0.12);
            }}
            div[data-testid="stTextInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stTextArea"] textarea {{
                min-height: 44px !important;
                font-size: 16px !important;
            }}
            /* Instagram-style fixed bottom tab bar — ONE horizontal row.
               IMPORTANT: do NOT use :has(marker) on stVerticalBlock for position:fixed —
               that matches the whole page root and clips expander content. */
            section.main .block-container {{
                padding-bottom: 7.25rem !important;
                padding-top: var(--ka-top-pad, 0.65rem) !important;
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
                position: relative !important;
            }}
            section.main {{
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
            }}
            /* Content blocks must never be fixed (that freezes scroll) */
            section.main div[data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host):not(.ka-theme-top-host) {{
                position: static !important;
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
            }}
            /* Fixed bottom dock — trailing empty column clears Streamlit Manage crown FAB */
            .ka-bottom-dock-host {{
                position: fixed !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                z-index: 2147483000 !important;
                width: 100vw !important;
                max-width: 100vw !important;
                height: auto !important;
                max-height: 7rem !important;
                margin: 0 !important;
                padding: 0.35rem 0.3rem calc(0.45rem + env(safe-area-inset-bottom, 0px)) 0.3rem !important;
                background: {c["main_bg"]} !important;
                border-top: 1px solid {c["border"]} !important;
                box-shadow: 0 -6px 20px rgba(15, 23, 42, 0.10) !important;
                pointer-events: auto !important;
                overflow: visible !important;
            }}
            .ka-bottom-dock-host [data-testid="stHorizontalBlock"] {{
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: stretch !important;
                justify-content: space-between !important;
                gap: 0.18rem !important;
                width: 100% !important;
                margin: 0 !important;
            }}
            .ka-bottom-dock-host [data-testid="stHorizontalBlock"] > div,
            .ka-bottom-dock-host [data-testid="column"],
            .ka-bottom-dock-host [data-testid="stColumn"] {{
                flex: 1 1 0 !important;
                min-width: 0 !important;
                max-width: none !important;
                width: auto !important;
            }}
            /* Last column = FAB spacer (not a tab) */
            .ka-bottom-dock-host [data-testid="stHorizontalBlock"] > div:last-child,
            .ka-bottom-dock-host [data-testid="column"]:last-child,
            .ka-bottom-dock-host [data-testid="stColumn"]:last-child {{
                flex: 0 0 4.75rem !important;
                max-width: 4.75rem !important;
                min-width: 4.5rem !important;
                pointer-events: none !important;
            }}
            .ka-dock-fab-spacer {{
                width: 100%;
                min-height: 3.35rem;
            }}
            .ka-bottom-dock-host button {{
                min-height: 3.45rem !important;
                width: 100% !important;
                white-space: pre-line !important;
                line-height: 1.12 !important;
                font-size: 0.72rem !important;
                font-weight: 700 !important;
                border-radius: 12px !important;
                padding: 0.32rem 0.12rem !important;
                transition: transform 0.12s ease, filter 0.12s ease !important;
                box-shadow: none !important;
            }}
            .ka-bottom-dock-host button:active {{
                transform: scale(0.88) !important;
                filter: brightness(0.9) !important;
            }}
            .ka-bottom-dock-host button:focus-visible {{
                outline: 2px solid {c["text"]}55 !important;
                outline-offset: 2px !important;
            }}
            /* Expanders must stay in normal flow (readable when opened) */
            [data-testid="stExpander"] {{
                overflow: visible !important;
            }}
            [data-testid="stExpanderDetails"],
            [data-testid="stExpander"] [data-testid="stVerticalBlock"] {{
                overflow: visible !important;
                max-height: none !important;
            }}
            div[data-testid="stVerticalBlock"]:has(.ka-checkin-bar-marker) {{
                background: {COLOR_WARN_BG};
                border: 1px solid {COLOR_WARN_BORDER};
                border-radius: {RADIUS};
                padding: 0.65rem 0.75rem;
                margin-bottom: 0.75rem;
            }}
            .ka-pwa-hint {{
                {pwa_hint_style}
                border-radius: {RADIUS};
                padding: 0.65rem 0.85rem;
                margin-bottom: 0.75rem;
                font-size: 0.85rem;
            }}
            .ka-pwa-hint-detail {{
                display: block;
                margin-top: 0.25rem;
                font-size: 0.78rem;
                color: {pwa_detail_style};
            }}
        }}
        /* Fixed top sub-tabs — same tile style as bottom dock (all widths) */
        section.main div[data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host):not(.ka-theme-top-host) {{
            position: static !important;
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
        }}
        section.main .block-container.ka-has-top-subtabs,
        section.main .block-container {{
            padding-top: var(--ka-top-pad, 0.65rem) !important;
        }}
        /* Top-right day / night theme toggle */
        .ka-theme-top-host {{
            position: fixed !important;
            top: 0.4rem !important;
            right: 0.4rem !important;
            left: auto !important;
            bottom: auto !important;
            z-index: 2147483644 !important;
            width: min(11.5rem, calc(100vw - 5.5rem)) !important;
            max-width: 11.5rem !important;
            height: auto !important;
            max-height: 3.6rem !important;
            margin: 0 !important;
            padding: 0.2rem !important;
            background: {c["main_bg"]} !important;
            border: 1px solid {c["border"]} !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.14) !important;
            pointer-events: auto !important;
            overflow: visible !important;
        }}
        .ka-theme-top-host [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.2rem !important;
            width: 100% !important;
            margin: 0 !important;
        }}
        .ka-theme-top-host [data-testid="stHorizontalBlock"] > div,
        .ka-theme-top-host [data-testid="column"],
        .ka-theme-top-host [data-testid="stColumn"] {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            max-width: none !important;
            width: auto !important;
        }}
        .ka-theme-top-host button {{
            min-height: 2.35rem !important;
            width: 100% !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            padding: 0.2rem 0.25rem !important;
            white-space: nowrap !important;
            box-shadow: none !important;
        }}
        .ka-top-subtab-host {{
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            top: 0 !important;
            z-index: 2147482900 !important;
            width: 100vw !important;
            max-width: 100vw !important;
            height: auto !important;
            max-height: 6.5rem !important;
            margin: 0 !important;
            padding: 0.35rem 0.35rem 0.4rem 0.35rem !important;
            background: {c["main_bg"]} !important;
            border-bottom: 1px solid {c["border"]} !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.10) !important;
            pointer-events: auto !important;
            overflow: visible !important;
        }}
        .ka-top-subtab-host [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            justify-content: space-between !important;
            gap: 0.2rem !important;
            width: 100% !important;
            margin: 0 !important;
        }}
        .ka-top-subtab-host [data-testid="stHorizontalBlock"] > div,
        .ka-top-subtab-host [data-testid="column"],
        .ka-top-subtab-host [data-testid="stColumn"] {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            max-width: none !important;
            width: auto !important;
        }}
        .ka-top-subtab-host button {{
            min-height: 3.15rem !important;
            width: 100% !important;
            white-space: pre-line !important;
            line-height: 1.12 !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 0.28rem 0.1rem !important;
            transition: transform 0.12s ease, filter 0.12s ease !important;
            box-shadow: none !important;
        }}
        .ka-top-subtab-host button:active {{
            transform: scale(0.88) !important;
            filter: brightness(0.9) !important;
        }}
        /* Markers stay in DOM; visually hidden */
        .ka-bottom-tabbar-marker,
        .ka-student-dock-marker,
        .ka-coach-dock-marker,
        .ka-top-subtab-marker,
        .ka-tab-tile {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}
        </style>
        <div class="{role_attr}" style="display:none"></div>
        """,
        unsafe_allow_html=True,
    )


def render_breadcrumb(*parts: str) -> None:
    if not parts:
        return
    trail = " › ".join(f"<span>{p}</span>" for p in parts[:-1])
    if trail:
        st.markdown(
            f'<div class="ka-breadcrumb">{trail} › <b>{parts[-1]}</b></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="ka-breadcrumb"><b>{parts[-1]}</b></div>', unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "") -> None:
    sub = f'<p class="ka-page-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<h1 class="ka-page-title">{title}</h1>{sub}',
        unsafe_allow_html=True,
    )


def render_stat_cards(items: list[tuple[str, str, str]]) -> None:
    """Render stat cards: [(label, value, tone)], tone = normal|warn|danger|success."""
    tones = {
        "normal": (None, None),
        "warn": (COLOR_WARN_BG, COLOR_WARN_BORDER),
        "danger": (COLOR_DANGER_BG, COLOR_DANGER_BORDER),
        "success": (COLOR_SUCCESS_BG, COLOR_SUCCESS_BORDER),
    }
    cards = []
    for label, value, tone in items:
        bg, border = tones.get(tone, tones["normal"])
        style = ""
        if bg:
            style = f' style="background:{bg};border-color:{border};"'
        cards.append(
            f'<div class="ka-stat-card"{style}>'
            f'<div class="ka-stat-label">{label}</div>'
            f'<div class="ka-stat-value">{value}</div></div>'
        )
    grid_cls = "ka-stat-grid ka-stat-grid-3" if len(items) == 3 else "ka-stat-grid"
    st.markdown(
        f'<div class="{grid_cls}">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_compact_bar(message: str, *, tone: str = "success") -> None:
    cls = "ka-bar-success" if tone == "success" else "ka-bar-warn"
    st.markdown(f'<div class="ka-bar {cls}">{message}</div>', unsafe_allow_html=True)


def render_empty_state(title: str, hint: str = "") -> None:
    hint_html = f'<div class="ka-empty-hint">{hint}</div>' if hint else ""
    st.markdown(
        f'<div class="ka-empty">'
        f'<div class="ka-empty-title">{title}</div>{hint_html}</div>',
        unsafe_allow_html=True,
    )
