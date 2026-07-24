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
# Dark main-content tokens — AMOLED page bg, grey surfaces so 方格 stand out
DARK = {
    "text": "#ffffff",
    "muted": "#ffffff",  # 夜光：次要文字也用白，避免與背景混在一起
    "border": "#666666",
    "card_bg": "#1a1a1a",
    "main_bg": "#000000",
    "primary": "#ffffff",
}
# Shared grey surface for form boxes / chips / buttons in 夜光
DARK_SURFACE = "#1a1a1a"
DARK_BORDER = "#666666"

COLOR_SUCCESS_BG = "#dcfce7"
COLOR_SUCCESS_BORDER = "#86efac"
COLOR_WARN_BG = "#fef3c7"
COLOR_WARN_BORDER = "#fcd34d"
COLOR_DANGER_BG = "#fee2e2"
COLOR_DANGER_BORDER = "#fca5a5"
RADIUS = "10px"


def get_ui_theme() -> str:
    t = st.session_state.get("ui_theme", "light")
    return t if t in ("light", "dark") else "light"


def get_ui_colors() -> dict[str, str]:
    """Current main-content theme tokens for inline HTML."""
    return dict(DARK if get_ui_theme() == "dark" else LIGHT)


def sync_ui_theme() -> str:
    """Keep ``ui_theme`` ↔ sidebar toggle in sync before CSS injection.

    Streamlit widget ``key`` can desync from a separate ``ui_theme`` flag when
    only ``on_change`` is used; reading the toggle every run is reliable.
    """
    if "ui_theme" not in st.session_state or st.session_state.ui_theme not in ("light", "dark"):
        st.session_state.ui_theme = "light"
    if "ui_theme_toggle" in st.session_state:
        st.session_state.ui_theme = "dark" if st.session_state.ui_theme_toggle else "light"
    else:
        st.session_state.ui_theme_toggle = st.session_state.ui_theme == "dark"
    return st.session_state.ui_theme


def sync_ui_density() -> str:
    """Keep ``ui_density`` ↔ comfortable toggle in sync (compact | comfortable)."""
    if st.session_state.get("ui_density") not in ("compact", "comfortable"):
        st.session_state.ui_density = "compact"
    if "ui_density_comfortable" in st.session_state:
        st.session_state.ui_density = (
            "comfortable" if st.session_state.ui_density_comfortable else "compact"
        )
    else:
        st.session_state.ui_density_comfortable = st.session_state.ui_density == "comfortable"
    return st.session_state.ui_density


def get_ui_density() -> str:
    d = st.session_state.get("ui_density", "compact")
    return d if d in ("compact", "comfortable") else "compact"


def render_theme_toggle() -> None:
    """Sidebar theme + density — also available via main-area quick buttons."""
    sync_ui_theme()
    sync_ui_density()
    st.toggle(
        "夜光模式（主內容變暗）",
        key="ui_theme_toggle",
        help="開啟＝夜光／關閉＝日間。側欄維持深色。",
        on_change=_sync_theme_from_toggle,
    )
    mode = "夜光" if get_ui_theme() == "dark" else "日間"
    st.caption(f"目前：{mode}")
    st.toggle(
        "舒適間距（較疏）",
        key="ui_density_comfortable",
        help="開啟＝加大垂直間距，減少誤觸；關閉＝緊湊。",
        on_change=_sync_density_from_toggle,
    )


def _flip_theme_quick() -> None:
    """Button on_click — must mutate widget keys *before* next run's widgets."""
    cur = st.session_state.get("ui_theme_toggle")
    if cur is None:
        cur = st.session_state.get("ui_theme") == "dark"
    st.session_state.ui_theme_toggle = not bool(cur)
    st.session_state.ui_theme = "dark" if st.session_state.ui_theme_toggle else "light"


def _flip_density_quick() -> None:
    """Button on_click — must mutate widget keys *before* next run's widgets."""
    cur = st.session_state.get("ui_density_comfortable")
    if cur is None:
        cur = st.session_state.get("ui_density") == "comfortable"
    st.session_state.ui_density_comfortable = not bool(cur)
    st.session_state.ui_density = (
        "comfortable" if st.session_state.ui_density_comfortable else "compact"
    )


def render_theme_density_quick() -> None:
    """Main-content day/night + density switches — no need to open ☰.

    Uses ``on_click`` so we never assign ``ui_theme_toggle`` /
    ``ui_density_comfortable`` after the sidebar toggles already exist
    (that raises StreamlitAPIException).
    """
    sync_ui_theme()
    sync_ui_density()
    is_dark = get_ui_theme() == "dark"
    is_comfy = get_ui_density() == "comfortable"
    c1, c2 = st.columns(2)
    with c1:
        st.button(
            "☀️ 日間" if is_dark else "🌙 夜光",
            key="ka_theme_quick_btn",
            use_container_width=True,
            help="切換主內容日間／夜光（唔使開側欄）",
            on_click=_flip_theme_quick,
        )
    with c2:
        st.button(
            "📐 緊湊" if is_comfy else "🖐️ 舒適",
            key="ka_density_quick_btn",
            use_container_width=True,
            help="切換緊湊／舒適間距",
            on_click=_flip_density_quick,
        )


def _sync_theme_from_toggle() -> None:
    st.session_state.ui_theme = "dark" if st.session_state.get("ui_theme_toggle") else "light"


def _sync_density_from_toggle() -> None:
    st.session_state.ui_density = (
        "comfortable" if st.session_state.get("ui_density_comfortable") else "compact"
    )


def inject_late_dark_overrides() -> None:
    """Inject dark-surface CSS last so it wins over Streamlit widget defaults.

    Only runs when ``ui_theme == dark`` (no ``body:has`` needed). Targets both
    legacy ``section.main`` and Streamlit 1.39+ ``stMain`` / ``[data-testid=stMain]``.
    """
    if get_ui_theme() != "dark":
        return
    s, b = DARK_SURFACE, DARK_BORDER
    main = ':is(section.main, section.stMain, [data-testid="stMain"])'
    css = f"""
    <style id="ka-late-dark-overrides">
    /* Form boxes: grey on black */
    {main} div[data-testid="stTextInput"] input,
    {main} div[data-testid="stNumberInput"] input,
    {main} div[data-testid="stDateInput"] input,
    {main} div[data-testid="stTimeInput"] input,
    {main} div[data-testid="stTextArea"] textarea,
    {main} div[data-baseweb="select"] > div,
    {main} div[data-baseweb="input"],
    {main} [data-testid="stExpander"],
    {main} [data-testid="stAlert"],
    {main} [data-testid="stTabs"] button,
    {main} code,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] input,
    [data-testid="stAppViewContainer"] div[data-testid="stNumberInput"] input,
    [data-testid="stAppViewContainer"] div[data-testid="stDateInput"] input,
    [data-testid="stAppViewContainer"] div[data-testid="stTextArea"] textarea,
    [data-testid="stAppViewContainer"] div[data-baseweb="select"] > div,
    [data-testid="stAppViewContainer"] div[data-baseweb="input"],
    [data-testid="stAppViewContainer"] [data-testid="stExpander"] {{
        background: {s} !important;
        background-color: {s} !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1px solid {b} !important;
        box-shadow: none !important;
        caret-color: #ffffff !important;
    }}
    {main} div[data-testid="stTextInput"] input::placeholder,
    {main} div[data-testid="stTextArea"] textarea::placeholder,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] input::placeholder,
    [data-testid="stAppViewContainer"] div[data-testid="stTextArea"] textarea::placeholder {{
        color: #999999 !important;
        -webkit-text-fill-color: #999999 !important;
        opacity: 1 !important;
    }}
    {main} [data-testid="stProgress"] > div {{
        background-color: {s} !important;
        border: 1px solid {b} !important;
    }}
    /* Select / date controls: BaseWeb inner layers stay white unless forced */
    {main} [data-testid="stSelectbox"] [data-baseweb="select"],
    {main} [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    {main} [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
    {main} [data-testid="stSelectbox"] [data-baseweb="select"] div,
    {main} [data-testid="stMultiSelect"] [data-baseweb="select"],
    {main} [data-testid="stMultiSelect"] [data-baseweb="select"] div,
    {main} [data-testid="stDateInput"] [data-baseweb="select"],
    {main} [data-testid="stDateInput"] [data-baseweb="select"] div,
    {main} [data-testid="stDateInput"] [data-baseweb="input"],
    {main} [data-testid="stDateInput"] [data-baseweb="input"] > div,
    {main} [data-testid="stTimeInput"] [data-baseweb="select"],
    {main} [data-testid="stTimeInput"] [data-baseweb="select"] div,
    [data-testid="stAppViewContainer"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stAppViewContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stAppViewContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
    [data-testid="stAppViewContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] div,
    [data-testid="stAppViewContainer"] [data-testid="stMultiSelect"] [data-baseweb="select"] div,
    [data-testid="stAppViewContainer"] [data-testid="stDateInput"] [data-baseweb="select"] div,
    [data-testid="stAppViewContainer"] [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stAppViewContainer"] [data-testid="stDateInput"] [data-baseweb="input"] > div {{
        background: {s} !important;
        background-color: {s} !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border-color: {b} !important;
        box-shadow: none !important;
    }}
    {main} [data-testid="stSelectbox"] [data-baseweb="select"] span,
    {main} [data-testid="stSelectbox"] [data-baseweb="select"] input,
    {main} [data-testid="stSelectbox"] svg,
    [data-testid="stAppViewContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
    [data-testid="stAppViewContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] input,
    [data-testid="stAppViewContainer"] [data-testid="stSelectbox"] svg {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        fill: #ffffff !important;
    }}
    /* Dropdown popover portals render under body, outside stMain */
    body div[data-baseweb="popover"],
    body div[data-baseweb="popover"] > div,
    body div[data-baseweb="menu"],
    body ul[role="listbox"],
    body li[role="option"],
    body [data-baseweb="menu"] li,
    body [data-baseweb="calendar"],
    body [data-baseweb="calendar"] div {{
        background: {s} !important;
        background-color: {s} !important;
        color: #ffffff !important;
        border-color: {b} !important;
    }}
    body li[role="option"]:hover,
    body li[aria-selected="true"],
    body [data-baseweb="menu"] li:hover {{
        background: #2a2a2a !important;
        background-color: #2a2a2a !important;
        color: #ffffff !important;
    }}
    /* All main text white — widget labels like「中文名 *」 */
    {main},
    {main} p,
    {main} span,
    {main} label,
    {main} label *,
    {main} [data-testid="stWidgetLabel"],
    {main} [data-testid="stWidgetLabel"] *,
    {main} [data-testid="stWidgetLabel"] [data-testid="stMarkdownContainer"] p,
    {main} [data-testid="stWidgetLabel"] [data-testid="stMarkdownContainer"] span,
    {main} .stTextInput label,
    {main} .stTextInput label *,
    {main} .stSelectbox label,
    {main} .stSelectbox label *,
    {main} .stTextArea label,
    {main} .stTextArea label *,
    {main} .stDateInput label,
    {main} .stDateInput label *,
    {main} .stNumberInput label,
    {main} .stNumberInput label *,
    {main} .stTimeInput label,
    {main} .stTimeInput label *,
    {main} [data-testid="stRadio"] label,
    {main} [data-testid="stRadio"] label *,
    {main} [data-testid="stCheckbox"] label,
    {main} [data-testid="stCheckbox"] label *,
    {main} [data-testid="stCaptionContainer"],
    {main} [data-testid="stCaptionContainer"] *,
    {main} [data-testid="stMarkdownContainer"],
    {main} [data-testid="stMarkdownContainer"] p,
    {main} [data-testid="stMarkdownContainer"] span,
    {main} [data-testid="stMarkdownContainer"] li,
    {main} [data-testid="stMarkdownContainer"] strong,
    {main} [data-testid="stMarkdownContainer"] h1,
    {main} [data-testid="stMarkdownContainer"] h2,
    {main} [data-testid="stMarkdownContainer"] h3,
    {main} .ka-breadcrumb,
    {main} .ka-breadcrumb *,
    {main} .ka-page-title,
    {main} .ka-page-sub,
    {main} [data-testid="stMetricLabel"],
    {main} [data-testid="stMetricLabel"] *,
    {main} [data-testid="stMetricValue"],
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"],
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] *,
    [data-testid="stAppViewContainer"] label[data-testid="stWidgetLabel"],
    [data-testid="stAppViewContainer"] label[data-testid="stWidgetLabel"] *,
    [data-testid="stAppViewContainer"] .stTextInput label,
    [data-testid="stAppViewContainer"] .stTextInput label *,
    [data-testid="stAppViewContainer"] .stSelectbox label,
    [data-testid="stAppViewContainer"] .stSelectbox label *,
    [data-testid="stAppViewContainer"] .stDateInput label,
    [data-testid="stAppViewContainer"] .stDateInput label *,
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    /* Buttons */
    [data-testid="stAppViewContainer"] [data-testid="stButton"] > button,
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button,
    .st-key-ka_theme_quick_btn [data-testid="stButton"] button,
    .st-key-ka_density_quick_btn [data-testid="stButton"] button,
    .ka-force-row-host [data-testid="stButton"] > button,
    .ka-bottom-dock-host [data-testid="stButton"] > button,
    .ka-top-subtab-host [data-testid="stButton"] > button {{
        background: {s} !important;
        background-color: {s} !important;
        color: #ffffff !important;
        border: 1px solid {b} !important;
        box-shadow: none !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button p,
    [data-testid="stAppViewContainer"] [data-testid="stButton"] button span,
    .ka-force-row-host button p,
    .ka-bottom-dock-host button p,
    .ka-top-subtab-host button p {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    .ka-bottom-dock-host button[kind="primary"],
    .ka-top-subtab-host button[kind="primary"],
    .ka-force-row-host button[kind="primary"] {{
        background: #ff4b4b !important;
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
        color: #ffffff !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stButton"] > button:hover,
    [data-testid="stAppViewContainer"] [data-testid="stButton"] > button:active,
    [data-testid="stAppViewContainer"] [data-testid="stButton"] > button:focus,
    [data-testid="stAppViewContainer"] [data-testid="stButton"] > button:focus-visible,
    .ka-bottom-dock-host button:hover,
    .ka-bottom-dock-host button:active,
    .ka-top-subtab-host button:hover,
    .ka-top-subtab-host button:active,
    .ka-force-row-host button:hover,
    .ka-force-row-host button:active {{
        background: {s} !important;
        background-color: {s} !important;
        color: #ffffff !important;
        border-color: {b} !important;
        filter: none !important;
        transform: none !important;
        outline: none !important;
        box-shadow: none !important;
    }}
    .ka-bottom-dock-host button[kind="primary"]:hover,
    .ka-bottom-dock-host button[kind="primary"]:active,
    .ka-top-subtab-host button[kind="primary"]:hover,
    .ka-top-subtab-host button[kind="primary"]:active,
    .ka-force-row-host button[kind="primary"]:hover,
    .ka-force-row-host button[kind="primary"]:active {{
        background: #ff4b4b !important;
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
    }}
    </style>
    """
    try:
        st.html(css)
    except Exception:
        st.markdown(css, unsafe_allow_html=True)


def inject_global_css(theme: str | None = None, role_class: str = "", **_kwargs) -> None:
    """Inject global CSS. role_class is optional (legacy callers may omit it)."""
    t = theme or sync_ui_theme()
    density = sync_ui_density()
    c = DARK if t == "dark" else LIGHT
    role_attr = f"ka-role-{role_class}" if role_class else ""
    # Marker class so we can verify which theme CSS is live in the DOM
    theme_marker = f"ka-theme-{t}"
    density_gap = "0.55rem" if density == "comfortable" else "0.28rem"

    if t == "dark":
        bar_success_style = f"background:{DARK_SURFACE};border:1px solid {DARK_BORDER};color:#ffffff;"
        bar_warn_style = f"background:{DARK_SURFACE};border:1px solid {DARK_BORDER};color:#ffffff;"
        pwa_hint_style = f"background:{DARK_SURFACE};border:1px solid {DARK_BORDER};color:#ffffff;"
        pwa_detail_style = "color:#cccccc;"
        sidebar_pending_style = f"background:{DARK_SURFACE};border:1px solid {DARK_BORDER};color:#ffffff;"
    else:
        bar_success_style = f"background:{COLOR_SUCCESS_BG};border:1px solid {COLOR_SUCCESS_BORDER};color:#166534;"
        bar_warn_style = f"background:{COLOR_WARN_BG};border:1px solid {COLOR_WARN_BORDER};color:#92400e;"
        pwa_hint_style = "background:#eff6ff;border:1px solid #93c5fd;color:#1e3a8a;"
        pwa_detail_style = "color:#475569;"
        sidebar_pending_style = f"background:{COLOR_WARN_BG};border:1px solid {COLOR_WARN_BORDER};color:#92400e;"

    dark_stat_override = ""
    if t == "dark":
        dark_stat_override = f"""
        .ka-stat-card {{ background: {DARK_SURFACE} !important; border: 1px solid {DARK_BORDER} !important; }}
        .ka-stat-value {{ color: #ffffff !important; }}
        .ka-stat-label {{ color: #ffffff !important; }}
        .ka-lb-card {{ background: {DARK_SURFACE} !important; border: 1px solid {DARK_BORDER} !important; color: #ffffff !important; }}
        .ka-empty {{ background: {DARK_SURFACE} !important; border: 1px dashed {DARK_BORDER} !important; }}
        .ka-empty-title, .ka-empty-hint {{ color: #ffffff !important; }}
        .ka-lb-meta {{ color: #ffffff !important; }}
        .ka-stat-card.ka-tone-success,
        .ka-stat-card.ka-tone-warn,
        .ka-stat-card.ka-tone-danger {{
          background: {DARK_SURFACE} !important;
          border: 1px solid {DARK_BORDER} !important;
        }}
        .ka-stat-card.ka-tone-success .ka-stat-value,
        .ka-stat-card.ka-tone-warn .ka-stat-value,
        .ka-stat-card.ka-tone-danger .ka-stat-value {{
          color: #ffffff !important;
        }}
        .ka-goal-wrap, .ka-goal-card {{
          background: {DARK_SURFACE} !important;
          border: 1px solid {DARK_BORDER} !important;
        }}
        .ka-goal-title, .ka-goal-event, .ka-goal-meta, .ka-goal-empty {{
          color: #ffffff !important;
        }}
        """

    # Theme-aware Streamlit chrome (alerts / inputs / metrics often stay light and become unreadable)
    if t == "dark":
        widget_contrast = f"""
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] {{
            background-color: {DARK_SURFACE} !important;
            border: 1px solid {DARK_BORDER} !important;
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"] strong,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"] li,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] span {{
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetricValue"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetricDelta"] {{
            color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetricLabel"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetricLabel"] p {{
            color: {c["muted"]} !important;
        }}
        /* 夜光表單方格：灰底，與全黑頁面分離 */
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stTextInput"] input,
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stNumberInput"] input,
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stDateInput"] input,
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stTimeInput"] input,
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stTextArea"] textarea {{
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
            caret-color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stTextInput"] input::placeholder,
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stTextArea"] textarea::placeholder {{
            color: #999999 !important;
            -webkit-text-fill-color: #999999 !important;
            opacity: 1 !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-baseweb="select"] > div,
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-baseweb="input"] {{
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stSelectbox"] [data-baseweb="select"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stSelectbox"] [data-baseweb="select"] div,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMultiSelect"] [data-baseweb="select"] div,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stDateInput"] [data-baseweb="select"] div,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stDateInput"] [data-baseweb="input"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stDateInput"] [data-baseweb="input"] > div {{
            background: {DARK_SURFACE} !important;
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border-color: {DARK_BORDER} !important;
            box-shadow: none !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-baseweb="select"] span,
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-baseweb="select"] input,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stSelectbox"] svg {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            fill: #ffffff !important;
        }}
        body:has(.ka-theme-dark) div[data-baseweb="popover"],
        body:has(.ka-theme-dark) div[data-baseweb="popover"] > div,
        body:has(.ka-theme-dark) div[data-baseweb="menu"],
        body:has(.ka-theme-dark) ul[role="listbox"],
        body:has(.ka-theme-dark) li[role="option"],
        body:has(.ka-theme-dark) [data-baseweb="calendar"],
        body:has(.ka-theme-dark) [data-baseweb="calendar"] div {{
            background: {DARK_SURFACE} !important;
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border-color: {DARK_BORDER} !important;
        }}
        body:has(.ka-theme-dark) li[role="option"]:hover,
        body:has(.ka-theme-dark) li[aria-selected="true"] {{
            background: #2a2a2a !important;
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stRadio"] label p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stCheckbox"] label p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stWidgetLabel"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stWidgetLabel"] p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stWidgetLabel"] span,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stWidgetLabel"] strong,
        :is(section.main, section.stMain, [data-testid="stMain"]) label[data-testid="stWidgetLabel"],
        :is(section.main, section.stMain, [data-testid="stMain"]) label[data-testid="stWidgetLabel"] * {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] {{
            background-color: {DARK_SURFACE} !important;
            border: 1px solid {DARK_BORDER} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] summary,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] summary p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] summary span {{
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stDataFrame"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stTable"] {{
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) .stMarkdown strong,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stMarkdown b,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] strong,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] b {{
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) code {{
            background: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stTabs"] button {{
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stTabs"] button p {{
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stTabs"] button[aria-selected="true"] {{
            border-width: 2px !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stProgress"] > div {{
            background-color: {DARK_SURFACE} !important;
            border: 1px solid {DARK_BORDER} !important;
        }}
        /* 夜光：主區按鈕 — 灰底、白字、灰邊 */
        :is(section.main, section.stMain, [data-testid="stMain"]) button,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stButton"] button,
        :is(section.main, section.stMain, [data-testid="stMain"]) button[kind="primary"],
        :is(section.main, section.stMain, [data-testid="stMain"]) button[kind="secondary"],
        :is(section.main, section.stMain, [data-testid="stMain"]) button[data-testid="baseButton-primary"],
        :is(section.main, section.stMain, [data-testid="stMain"]) button[data-testid="baseButton-secondary"] {{
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
            box-shadow: none !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) button p,
        :is(section.main, section.stMain, [data-testid="stMain"]) button span,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stButton"] button p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stButton"] button span,
        :is(section.main, section.stMain, [data-testid="stMain"]) button div[data-testid="stMarkdownContainer"] p {{
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) button[kind="primary"],
        :is(section.main, section.stMain, [data-testid="stMain"]) button[data-testid="baseButton-primary"] {{
            border-width: 2px !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) .ka-sidebar-open-btn,
        .ka-sidebar-open-btn {{
            background: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
            box-shadow: 0 4px 14px rgba(255, 255, 255, 0.12) !important;
        }}
        /* 夜光：底部／頂部導航、快速切換列 — 覆蓋 Streamlit secondary 白底 */
        body:has(.ka-theme-dark) .ka-bottom-dock-host [data-testid="stButton"] > button[kind="secondary"],
        body:has(.ka-theme-dark) .ka-bottom-dock-host button[kind="secondary"],
        body:has(.ka-theme-dark) .ka-top-subtab-host [data-testid="stButton"] > button[kind="secondary"],
        body:has(.ka-theme-dark) .ka-top-subtab-host button[kind="secondary"],
        body:has(.ka-theme-dark) .ka-force-row-host [data-testid="stButton"] > button[kind="secondary"],
        body:has(.ka-theme-dark) .ka-force-row-host button[kind="secondary"],
        body:has(.ka-theme-dark) .ka-bottom-dock-host [data-testid="stButton"] > button[data-testid="baseButton-secondary"],
        body:has(.ka-theme-dark) .ka-top-subtab-host [data-testid="stButton"] > button[data-testid="baseButton-secondary"],
        body:has(.ka-theme-dark) .ka-force-row-host [data-testid="stButton"] > button[data-testid="baseButton-secondary"] {{
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
            box-shadow: none !important;
        }}
        body:has(.ka-theme-dark) .ka-bottom-dock-host button[kind="secondary"] p,
        body:has(.ka-theme-dark) .ka-top-subtab-host button[kind="secondary"] p,
        body:has(.ka-theme-dark) .ka-force-row-host button[kind="secondary"] p {{
            color: #ffffff !important;
        }}
        /* 夜光：主區一般 secondary 按鈕（日間／夜光、舒適間距等） */
        body:has(.ka-theme-dark) :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stButton"] > button[kind="secondary"],
        body:has(.ka-theme-dark) :is(section.main, section.stMain, [data-testid="stMain"]) button[kind="secondary"],
        body:has(.ka-theme-dark) :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stButton"] > button[data-testid="baseButton-secondary"],
        body:has(.ka-theme-dark) :is(section.main, section.stMain, [data-testid="stMain"]) button[data-testid="baseButton-secondary"] {{
            background-color: {DARK_SURFACE} !important;
            color: #ffffff !important;
            border: 1px solid {DARK_BORDER} !important;
            box-shadow: none !important;
        }}
        body:has(.ka-theme-dark) :is(section.main, section.stMain, [data-testid="stMain"]) button[kind="secondary"] p,
        body:has(.ka-theme-dark) :is(section.main, section.stMain, [data-testid="stMain"]) button[data-testid="baseButton-secondary"] p {{
            color: #ffffff !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stVerticalBlock"]:has(.ka-checkin-bar-marker) {{
            background: {DARK_SURFACE} !important;
            border: 1px solid {DARK_BORDER} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stHeader"],
        header[data-testid="stHeader"] {{
            background: #000000 !important;
        }}
        """
    else:
        widget_contrast = f"""
        /* Light mode: keep alert semantic colors — do NOT force theme text onto pale alert fills */
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] [data-testid="stMarkdownContainer"] strong {{
            color: #0f172a !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetricValue"] {{
            color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetricLabel"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetricLabel"] p {{
            color: {c["muted"]} !important;
        }}
        .ka-lb-meta {{ color: {c["muted"]} !important; }}
        """

    st.markdown(
        f"""
        <style>
        /* Force main surfaces — Streamlit defaults override without !important */
        html, body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewBlockContainer"],
        :is(section.main, section.stMain, [data-testid="stMain"]),
        :is(section.main, section.stMain, [data-testid="stMain"]) .block-container {{
            background-color: {c["main_bg"]} !important;
            color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) .block-container {{
            padding-top: 0.65rem;
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
        hr {{ margin: 0.45rem 0; border-color: {c["border"]}; }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h1,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h2,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h3,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h4,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h5,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h6 {{
            color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] li,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] span {{
            color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stCaptionContainer"],
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stCaptionContainer"] p,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stCaptionContainer"] small {{
            color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) label[data-testid="stWidgetLabel"],
        :is(section.main, section.stMain, [data-testid="stMain"]) label[data-testid="stWidgetLabel"] p,
        :is(section.main, section.stMain, [data-testid="stMain"]) label[data-testid="stWidgetLabel"] span,
        :is(section.main, section.stMain, [data-testid="stMain"]) label[data-testid="stWidgetLabel"] strong,
        :is(section.main, section.stMain, [data-testid="stMain"]) label[data-testid="stWidgetLabel"] *,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stSelectbox label,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stSelectbox label p,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stSelectbox label span,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTextInput label,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTextInput label p,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTextInput label span,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTextArea label,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTextArea label p,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTextArea label span,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stDateInput label,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stDateInput label p,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stDateInput label span,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stNumberInput label,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stNumberInput label p,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTimeInput label,
        :is(section.main, section.stMain, [data-testid="stMain"]) .stTimeInput label p {{
            color: {c["text"]} !important;
            -webkit-text-fill-color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] summary,
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] summary p {{
            color: {c["text"]} !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p {{
            color: {c["text"]};
        }}
        {widget_contrast}
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
            color: {c["muted"]} !important;
            margin-bottom: 0.35rem;
        }}
        .ka-breadcrumb span {{ color: {c["muted"]} !important; }}
        .ka-breadcrumb b {{ color: {c["text"]} !important; font-weight: 600; }}
        .ka-page-title {{
            margin: 0;
            font-size: 1.55rem;
            font-weight: 800;
            color: {c["text"]} !important;
            letter-spacing: -0.01em;
        }}
        .ka-page-sub {{
            margin: 0.2rem 0 0;
            font-size: 0.88rem;
            color: {c["muted"]} !important;
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
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
                gap: 0.4rem !important;
            }}
            .ka-stat-grid-3 .ka-stat-card:last-child:nth-child(odd) {{
                grid-column: 1 / -1;
            }}
            .ka-stat-grid-3 .ka-stat-value {{ font-size: 1.05rem !important; }}
            .ka-stat-grid-3 .ka-stat-label {{ font-size: 0.68rem !important; }}
            .ka-page-title {{ font-size: 1.2rem !important; }}
            .ka-page-title.ka-page-title-compact {{
                font-size: 1.02rem !important;
                margin: 0.1rem 0 0.05rem 0 !important;
            }}
            .ka-page-sub.ka-page-sub-compact {{
                font-size: 0.72rem !important;
                margin: 0 0 0.15rem 0 !important;
            }}
            .block-container.ka-has-top-subtabs .ka-breadcrumb {{
                display: none !important;
            }}
            .ka-pending-mobile-banner {{
                position: sticky;
                top: var(--ka-top-pad, 4.2rem);
                z-index: 20;
                box-shadow: 0 4px 14px rgba(0,0,0,0.12);
            }}
            div[data-testid="stTextInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stTextArea"] textarea {{
                min-height: 40px !important;
                font-size: 16px !important;
            }}

            /*
             * Dense mobile layout — cut Streamlit's default vertical air
             * across all pages (檢視／時間／設定／總覽…).
             */
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host) {{
                gap: {density_gap} !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]).ka-density-comfortable [data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host) {{
                gap: {density_gap} !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stElementContainer"] {{
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] {{
                margin-bottom: 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] > * {{
                margin-top: 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] p {{
                margin: 0 0 0.2rem 0 !important;
                line-height: 1.35 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h1,
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h2,
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h3,
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMarkdownContainer"] h4 {{
                margin: 0.2rem 0 0.15rem 0 !important;
                line-height: 1.25 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stCaptionContainer"],
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stCaption"] {{
                margin: 0 0 0.1rem 0 !important;
                line-height: 1.3 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stHeadingWithActionElements"],
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stHeader"] {{
                margin: 0 0 0.15rem 0 !important;
                padding: 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stButton"] {{
                margin: 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stMetric"] {{
                margin: 0 !important;
                padding: 0.15rem 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stAlert"] {{
                margin: 0.15rem 0 !important;
                padding: 0.4rem 0.55rem !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stWidgetLabel"] {{
                margin-bottom: 0.05rem !important;
                min-height: 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) [data-testid="stExpander"] {{
                margin: 0.2rem 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) hr {{
                margin: 0.4rem 0 !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stDivider"] {{
                margin: 0.35rem 0 !important;
                padding: 0 !important;
            }}
            /* Chip / action strips — less outer chrome */
            :is(section.main, section.stMain, [data-testid="stMain"]) [class*="st-key-"] {{
                margin-top: 0.1rem !important;
                margin-bottom: 0.25rem !important;
            }}

            /* Instagram-style fixed bottom tab bar — ONE horizontal row.
               IMPORTANT: do NOT use :has(marker) on stVerticalBlock for position:fixed —
               that matches the whole page root and clips expander content. */
            :is(section.main, section.stMain, [data-testid="stMain"]) .block-container {{
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
                padding-bottom: 6.4rem !important;
                padding-top: var(--ka-top-pad, 0.4rem) !important;
                height: auto !important;
                max-height: none !important;
                overflow-x: hidden !important;
                overflow-y: visible !important;
                max-width: 100% !important;
                position: relative !important;
            }}
            :is(section.main, section.stMain, [data-testid="stMain"]) {{
                height: auto !important;
                max-height: none !important;
                overflow-x: hidden !important;
                overflow-y: visible !important;
                max-width: 100% !important;
            }}
            /* Content blocks must never be fixed (that freezes scroll) */
            :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host) {{
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
                width: 100% !important;
                max-width: 100% !important;
                height: auto !important;
                max-height: 7rem !important;
                margin: 0 !important;
                padding: 0.25rem 0.25rem calc(0.35rem + env(safe-area-inset-bottom, 0px)) 0.25rem !important;
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
            body:has(.ka-theme-dark) .ka-bottom-dock-host button:active,
            body:has(.ka-theme-dark) .ka-top-subtab-host button:active {{
                transform: none !important;
                filter: none !important;
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
        :is(section.main, section.stMain, [data-testid="stMain"]) div[data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host) {{
            position: static !important;
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
        }}
        :is(section.main, section.stMain, [data-testid="stMain"]) .block-container.ka-has-top-subtabs,
        :is(section.main, section.stMain, [data-testid="stMain"]) .block-container {{
            padding-top: var(--ka-top-pad, 0.65rem) !important;
        }}
        .ka-top-subtab-host {{
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            top: 0 !important;
            z-index: 2147482900 !important;
            width: 100% !important;
            max-width: 100% !important;
            height: auto !important;
            max-height: 6.5rem !important;
            margin: 0 !important;
            padding: 0.22rem 0.3rem 0.28rem 0.3rem !important;
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
            min-height: 3.2rem !important;
            width: 100% !important;
            white-space: pre-line !important;
            line-height: 1.15 !important;
            font-size: clamp(0.7rem, 2.9vw, 0.84rem) !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 0.32rem 0.15rem !important;
            transition: transform 0.12s ease, filter 0.12s ease !important;
            box-shadow: none !important;
        }}
        .ka-top-subtab-host button:active {{
            transform: scale(0.88) !important;
            filter: brightness(0.9) !important;
        }}
        body:has(.ka-theme-dark) .ka-top-subtab-host button:active {{
            transform: none !important;
            filter: none !important;
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
        <div class="{role_attr} {theme_marker} ka-density-{density}" data-ka-theme="{t}" data-ka-density="{density}" style="display:none"></div>
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


def render_page_header(title: str, subtitle: str = "", *, compact: bool = False) -> None:
    title_cls = "ka-page-title ka-page-title-compact" if compact else "ka-page-title"
    sub_cls = "ka-page-sub ka-page-sub-compact" if compact else "ka-page-sub"
    sub = f'<p class="{sub_cls}">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<h1 class="{title_cls}">{title}</h1>{sub}',
        unsafe_allow_html=True,
    )


def render_stat_cards(items: list[tuple[str, str, str]]) -> None:
    """Render stat cards: [(label, value, tone)], tone = normal|warn|danger|success."""
    tones = {
        "normal": (None, None, ""),
        "warn": (COLOR_WARN_BG, COLOR_WARN_BORDER, "ka-tone-warn"),
        "danger": (COLOR_DANGER_BG, COLOR_DANGER_BORDER, "ka-tone-danger"),
        "success": (COLOR_SUCCESS_BG, COLOR_SUCCESS_BORDER, "ka-tone-success"),
    }
    cards = []
    for label, value, tone in items:
        bg, border, tone_cls = tones.get(tone, tones["normal"])
        style = ""
        if bg and get_ui_theme() != "dark":
            style = f' style="background:{bg};border-color:{border};"'
        cls = f"ka-stat-card {tone_cls}".strip()
        cards.append(
            f'<div class="{cls}"{style}>'
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
