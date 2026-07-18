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


def render_theme_toggle() -> None:
    dark = st.toggle(
        "深色主內容區",
        value=get_ui_theme() == "dark",
        key="ui_theme_toggle",
        help="切換主內容區深/淺色（側欄維持深色）",
    )
    theme = "dark" if dark else "light"
    if st.session_state.get("ui_theme") != theme:
        st.session_state.ui_theme = theme
        st.rerun()


def inject_global_css(theme: str | None = None) -> None:
    t = theme or get_ui_theme()
    c = DARK if t == "dark" else LIGHT

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
            padding-top: 1rem;
        }}
        section.main {{
            background-color: {c["main_bg"]};
        }}
        hr {{ margin: 0.75rem 0; border-color: {c["border"]}; }}
        .ka-nav-label {{
            margin: 14px 0 6px;
            font-size: 11px;
            font-weight: 700;
            color: {c["muted"]};
            letter-spacing: 0.04em;
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
        .ka-stat-card {{
            background: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS};
            padding: 0.85rem 1rem;
        }}
        .ka-stat-label {{
            font-size: 0.75rem;
            color: {c["muted"]};
            margin-bottom: 0.25rem;
        }}
        .ka-stat-value {{
            font-size: 1.35rem;
            font-weight: 800;
            color: {c["text"]};
            line-height: 1.2;
        }}
        .ka-bar {{
            border-radius: {RADIUS};
            padding: 0.55rem 0.85rem;
            font-size: 0.88rem;
            margin-bottom: 0.75rem;
        }}
        .ka-bar-success {{
            background: {COLOR_SUCCESS_BG};
            border: 1px solid {COLOR_SUCCESS_BORDER};
            color: #166534;
        }}
        .ka-bar-warn {{
            background: {COLOR_WARN_BG};
            border: 1px solid {COLOR_WARN_BORDER};
            color: #92400e;
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
            background: {COLOR_WARN_BG};
            border: 1px solid {COLOR_WARN_BORDER};
            border-radius: {RADIUS};
            padding: 0.65rem 0.75rem;
            margin-bottom: 0.35rem;
            color: #92400e;
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
        {dark_stat_override}
        @media (max-width: 768px) {{
            .ka-stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
            section.main .block-container {{
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }}
            div[data-testid="stRadio"] label p {{
                font-size: 0.85rem !important;
            }}
        }}
        </style>
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
    st.markdown(
        f'<div class="ka-stat-grid">{"".join(cards)}</div>',
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
