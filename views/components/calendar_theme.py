"""Unified calendar color system — grid, list, legend; light & dark aware."""
from __future__ import annotations

import streamlit as st

from views.components.theme import get_ui_theme

# ── Light surfaces ────────────────────────────────────────────────────────
_LIGHT = {
    "grid_gutter": "#B8C4D4",
    "cell_bg": "#FFFFFF",
    "cell_empty_bg": "#E8EDF3",
    "cell_disabled_bg": "#DDE3EB",
    "list_card_bg": "#FFFFFF",
    "list_card_border": "#C5CED8",
    "text_primary": "#111827",
    "text_secondary": "#374151",
    "text_muted": "#5B6573",
    "cell_border": "#D1D9E2",
    "rest_border": "#C5CED8",
    "inset_highlight": "rgba(255,255,255,0.35)",
    "cell_shadow": "rgba(17,24,39,0.06)",
    "list_shadow": "rgba(17,24,39,0.07)",
}

# ── Dark surfaces (main content dark mode) ────────────────────────────────
_DARK = {
    "grid_gutter": "#2a3140",
    "cell_bg": "#1a1d24",
    "cell_empty_bg": "#141820",
    "cell_disabled_bg": "#12151c",
    "list_card_bg": "#1a1d24",
    "list_card_border": "#334155",
    "text_primary": "#e2e8f0",
    "text_secondary": "#cbd5e1",
    "text_muted": "#94a3b8",
    "cell_border": "#334155",
    "rest_border": "#475569",
    "inset_highlight": "rgba(255,255,255,0.06)",
    "cell_shadow": "rgba(0,0,0,0.25)",
    "list_shadow": "rgba(0,0,0,0.3)",
}

TEXT_ON_ACCENT = "#FFFFFF"
ACCENT_TODAY = "#1565C0"
ACCENT_SELECTED = "#1565C0"
ACCENT_SELECTED_TINT_LIGHT = "#E8F2FC"
ACCENT_SELECTED_TINT_DARK = "#1e3a5f"
ACCENT_SELECTED_RING = "#1565C0"

# Legacy module-level aliases (light defaults for helpers outside CSS injection)
GRID_GUTTER = _LIGHT["grid_gutter"]
CELL_BG = _LIGHT["cell_bg"]
CELL_EMPTY_BG = _LIGHT["cell_empty_bg"]
CELL_DISABLED_BG = _LIGHT["cell_disabled_bg"]
LIST_CARD_BG = _LIGHT["list_card_bg"]
LIST_CARD_BORDER = _LIGHT["list_card_border"]
TEXT_PRIMARY = _LIGHT["text_primary"]
TEXT_SECONDARY = _LIGHT["text_secondary"]
TEXT_MUTED = _LIGHT["text_muted"]

# ── Event tones: bg / fg / left-accent / border ───────────────────────────
CALENDAR_TONES: dict[str, dict[str, str]] = {
    "training": {
        "bg": "#B8D4F8",
        "fg": "#082F5C",
        "accent": "#1565C0",
        "border": "#6FA3DB",
    },
    "competition": {
        "bg": "#FFCACA",
        "fg": "#7F0D0D",
        "accent": "#C62828",
        "border": "#E07070",
    },
    "rest": {
        "bg": "#D5DCE5",
        "fg": "#2D3748",
        "accent": "#546E7A",
        "border": "#A0AEC0",
    },
    "empty": {
        "bg": "#E4E9EF",
        "fg": "#4A5568",
        "accent": "#718096",
        "border": "#CBD5E0",
    },
    "picked": {
        "bg": "#B8EBD0",
        "fg": "#065F46",
        "accent": "#059669",
        "border": "#6EE7B7",
    },
    "disabled": {
        "bg": "#DDE3EB",
        "fg": "#9CA3AF",
        "accent": "#CBD5E0",
        "border": "#C5CED8",
    },
}

CALENDAR_TONES_DARK: dict[str, dict[str, str]] = {
    "training": {
        "bg": "#1e3a5f",
        "fg": "#bfdbfe",
        "accent": "#3b82f6",
        "border": "#2563eb",
    },
    "competition": {
        "bg": "#450a0a",
        "fg": "#fecaca",
        "accent": "#ef4444",
        "border": "#b91c1c",
    },
    "rest": {
        "bg": "#1e293b",
        "fg": "#cbd5e1",
        "accent": "#64748b",
        "border": "#475569",
    },
    "empty": {
        "bg": "#141820",
        "fg": "#94a3b8",
        "accent": "#64748b",
        "border": "#334155",
    },
    "picked": {
        "bg": "#064e3b",
        "fg": "#a7f3d0",
        "accent": "#10b981",
        "border": "#059669",
    },
    "disabled": {
        "bg": "#12151c",
        "fg": "#64748b",
        "accent": "#334155",
        "border": "#1e293b",
    },
}

CALENDAR_BG_TRAINING = CALENDAR_TONES["training"]["bg"]
CALENDAR_BG_COMPETITION = CALENDAR_TONES["competition"]["bg"]
CALENDAR_BG_REST = CALENDAR_TONES["rest"]["bg"]
CALENDAR_BG_EMPTY = CELL_EMPTY_BG


def get_calendar_palette(theme: str | None = None) -> dict[str, str]:
    t = theme or get_ui_theme()
    return dict(_DARK if t == "dark" else _LIGHT)


def get_calendar_tones(theme: str | None = None) -> dict[str, dict[str, str]]:
    t = theme or get_ui_theme()
    return CALENDAR_TONES_DARK if t == "dark" else CALENDAR_TONES


def compact_tone_styles(theme: str | None = None) -> dict[str, tuple[str, str, str]]:
    """(background, foreground, border) for square-grid calendar buttons."""
    tones = get_calendar_tones(theme)
    return {
        tone: (t["bg"], t["fg"], t["border"])
        for tone, t in tones.items()
    } | {
        "attended": (
            tones["picked"]["bg"],
            tones["picked"]["fg"],
            tones["picked"]["border"],
        ),
    }


def _chip_rules(parent: str, tones: dict[str, dict[str, str]], *, compact: bool = False) -> str:
    fs = "0.56rem" if compact else "0.8rem"
    pad = "2px 4px" if compact else "6px 10px"
    radius = "4px" if compact else "7px"
    border_w = "3px" if compact else "4px"
    rules: list[str] = []
    for tone, t in tones.items():
        if tone in ("picked", "disabled"):
            continue
        rules.append(
            f"{parent} .ka-tt-chip-{tone} {{"
            f"background:{t['bg']} !important;"
            f"color:{t['fg']} !important;"
            f"border-left:{border_w} solid {t['accent']} !important;"
            f"border-top:1px solid {t['border']} !important;"
            f"border-right:1px solid {t['border']} !important;"
            f"border-bottom:1px solid {t['border']} !important;"
            f"font-size:{fs}; font-weight:700; line-height:1.25;"
            f"padding:{pad}; border-radius:{radius};"
            f"}}"
        )
    return "\n".join(rules)


def build_calendar_theme_css(theme: str | None = None) -> str:
    p = get_calendar_palette(theme)
    tones = get_calendar_tones(theme)
    selected_tint = ACCENT_SELECTED_TINT_DARK if (theme or get_ui_theme()) == "dark" else ACCENT_SELECTED_TINT_LIGHT
    t_train = tones["training"]
    t_comp = tones["competition"]
    t_rest = tones["rest"]
    t_picked = tones["picked"]
    # Scope list overlay CSS away from page chrome (view toggle / month nav)
    _lh = (
        'div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap)'
        ":not(:has(.ka-cal-view-marker))"
        ":not(:has(.ka-cal-month-nav-marker))"
        ":not(:has(.ka-coach-screen-marker))"
    )

    return f"""
:root {{
    --ka-cal-grid: {p['grid_gutter']};
    --ka-cal-cell: {p['cell_bg']};
    --ka-cal-text: {p['text_primary']};
    --ka-cal-muted: {p['text_muted']};
    --ka-cal-today: {ACCENT_TODAY};
    --ka-cal-selected: {ACCENT_SELECTED_RING};
}}

.ka-cal-month-title {{
    text-align: center;
    margin: 0;
    font-size: 1.25rem;
    font-weight: 800;
    color: {p['text_primary']} !important;
    letter-spacing: -0.01em;
}}

/* ── Legend ── */
div[data-testid="stVerticalBlock"]:has(.ka-cal-legend-marker) .ka-cal-legend {{
    display: flex; flex-wrap: wrap; gap: 8px; margin: 0.35rem 0 0.75rem;
}}
div[data-testid="stVerticalBlock"]:has(.ka-cal-legend-marker) .ka-cal-legend span {{
    font-size: 0.78rem; font-weight: 700; padding: 6px 12px;
    border-radius: 8px; border: 1px solid transparent;
}}
.ka-leg-training {{
    background: {t_train['bg']} !important; color: {t_train['fg']} !important;
    border-color: {t_train['border']} !important;
}}
.ka-leg-competition {{
    background: {t_comp['bg']} !important; color: {t_comp['fg']} !important;
    border-color: {t_comp['border']} !important;
}}
.ka-leg-rest {{
    background: {t_rest['bg']} !important; color: {t_rest['fg']} !important;
    border-color: {t_rest['border']} !important;
}}

/* ── Calendar shell (streamlit-extras stylable_container) ── */
div[data-testid="stVerticalBlock"]:has(.ka-cal-shell-marker) > div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: {p['list_card_border']} !important;
    background: {p['cell_bg']} !important;
}}

/* ── Month grid layout ──
 * Markers must be *inside* the row's columns (:has on stHorizontalBlock).
 * Also match .ka-tt-marker / .ka-tt-empty so day rows stay 7-across on mobile.
 */
div[data-testid="stHorizontalBlock"]:has(.ka-tt-grid-marker),
div[data-testid="stHorizontalBlock"]:has(.ka-tt-hdr),
div[data-testid="stHorizontalBlock"]:has(.ka-tt-marker),
div[data-testid="stHorizontalBlock"]:has(.ka-tt-empty) {{
    display: grid !important;
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    gap: 3px !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    max-width: 100% !important;
    background: {p['grid_gutter']} !important;
    border-radius: 12px !important;
    padding: 3px !important;
    box-shadow: inset 0 1px 0 {p['inset_highlight']};
}}
div[data-testid="stHorizontalBlock"]:has(.ka-tt-grid-marker) > div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.ka-tt-hdr) > div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.ka-tt-marker) > div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.ka-tt-empty) > div[data-testid="column"] {{
    padding: 0 !important; margin: 0 !important; min-width: 0 !important;
    max-width: none !important; width: auto !important; flex: unset !important;
}}

div[data-testid="column"]:has(.ka-tt-marker) {{
    position: relative !important; min-height: 5rem !important;
}}
div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stVerticalBlock"] {{
    position: relative !important; min-height: 5rem !important; gap: 0 !important;
}}

div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell {{
    position: absolute; inset: 0;
    background: {p['cell_bg']};
    border: 1px solid {p['cell_border']};
    border-radius: 8px;
    padding: 4px 3px 3px;
    display: flex; flex-direction: column; gap: 3px;
    overflow: hidden; box-sizing: border-box;
    pointer-events: none; z-index: 1;
    box-shadow: 0 1px 2px {p['cell_shadow']};
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell.ka-tt-selected {{
    background: {selected_tint};
    box-shadow: inset 0 0 0 2px {ACCENT_SELECTED_RING}, 0 1px 3px rgba(21,101,192,0.15);
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell.ka-tt-today {{
    border-color: {ACCENT_TODAY};
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell.ka-tt-today .ka-tt-daynum {{
    background: {ACCENT_TODAY}; color: {TEXT_ON_ACCENT};
    border-radius: 999px; width: 1.45rem; height: 1.45rem;
    display: inline-flex; align-items: center; justify-content: center; font-weight: 800;
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-daynum {{
    font-size: 0.78rem; font-weight: 800; color: {p['text_primary']};
    line-height: 1.2; padding-left: 2px; flex-shrink: 0;
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chips {{
    display: flex; flex-direction: column; gap: 3px;
    flex: 1; min-height: 0; overflow: hidden;
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip {{
    display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
{_chip_rules('div[data-testid="column"]:has(.ka-tt-marker)', tones, compact=True)}

div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-more {{
    font-size: 0.52rem; color: {p['text_secondary']}; font-weight: 800; padding-left: 3px;
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-pick {{
    position: absolute; top: 3px; right: 3px;
    font-size: 0.58rem; font-weight: 800; color: {t_picked['accent']};
    background: {t_picked['bg']}; padding: 1px 4px; border-radius: 4px;
    z-index: 2; pointer-events: none;
}}
div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stButton"] {{
    position: absolute !important; inset: 0 !important; z-index: 4 !important;
    height: 100% !important; margin: 0 !important; padding: 0 !important;
}}
div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stButton"] button {{
    opacity: 0 !important; width: 100% !important; height: 100% !important;
    min-height: 5rem !important; margin: 0 !important; padding: 0 !important; border: none !important;
}}
div[data-testid="column"]:has(.ka-tt-marker[data-disabled="1"]) .ka-tt-cell {{
    background: {p['cell_disabled_bg']}; border-color: {p['rest_border']};
}}
div[data-testid="column"]:has(.ka-tt-marker[data-disabled="1"]) .ka-tt-daynum {{
    color: {p['text_muted']};
}}
div[data-testid="column"]:has(.ka-tt-hdr) p {{
    text-align: center !important; font-size: 0.7rem !important;
    margin: 0 !important; padding: 5px 0 !important;
    color: {p['text_secondary']} !important; font-weight: 800 !important;
    background: {p['cell_bg']}; border-radius: 6px;
}}
div[data-testid="column"]:has(.ka-tt-empty) {{
    min-height: 5rem !important; background: {p['cell_empty_bg']};
    border-radius: 8px; border: 1px solid {p['cell_border']};
}}

/* ── List / agenda cards ── */
{_lh} {{
    position: relative; margin-bottom: 0.45rem;
}}
{_lh} .ka-tt-list-card {{
    background: {p['list_card_bg']};
    border: 1px solid {p['list_card_border']};
    border-radius: 12px; padding: 12px 14px;
    pointer-events: none;
    box-shadow: 0 1px 3px {p['list_shadow']};
}}
{_lh} .ka-tt-list-card.ka-tt-list-active {{
    border-color: {ACCENT_SELECTED_RING};
    background: {selected_tint};
    box-shadow: inset 0 0 0 1px {ACCENT_SELECTED_RING}, 0 2px 6px rgba(21,101,192,0.12);
}}
{_lh} .ka-tt-list-head {{
    display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}}
{_lh} .ka-tt-list-date {{
    font-size: 1.05rem; font-weight: 800; color: {p['text_primary']};
}}
{_lh} .ka-tt-list-wd {{
    font-size: 0.85rem; color: {p['text_secondary']}; font-weight: 700;
}}
{_lh} .ka-tt-list-today-tag {{
    font-size: 0.7rem; background: {ACCENT_TODAY}; color: {TEXT_ON_ACCENT};
    padding: 3px 9px; border-radius: 999px; font-weight: 800;
}}
{_lh} .ka-tt-list-chips {{
    display: flex; flex-direction: column; gap: 5px;
}}
{_lh} .ka-tt-chip {{
    display: block;
}}
{_chip_rules(_lh, tones, compact=False)}

{_lh} .ka-tt-list-rest {{
    font-size: 0.85rem; color: {p['text_muted']}; font-weight: 700;
    padding: 6px 10px; background: {p['cell_empty_bg']}; border-radius: 7px;
    border: 1px dashed {p['rest_border']};
}}
{_lh} .ka-tt-list-detail {{
    font-size: 0.78rem; color: {p['text_secondary']}; margin-top: 8px; font-weight: 600;
}}
{_lh} [data-testid="stButton"] {{
    position: absolute !important; inset: 0 !important; z-index: 2 !important;
}}
{_lh} [data-testid="stButton"] button {{
    opacity: 0 !important; width: 100% !important; height: 100% !important;
    min-height: 3.75rem !important;
}}

/* View toggle — never hide 日曆 / 列表 labels */
div[data-testid="stVerticalBlock"]:has(.ka-cal-view-marker) [data-testid="stButton"] {{
    position: static !important;
    inset: auto !important;
}}
div[data-testid="stVerticalBlock"]:has(.ka-cal-view-marker) button {{
    opacity: 1 !important;
    visibility: visible !important;
    color: {p['text_primary']} !important;
    font-weight: 800 !important;
    min-height: 2.75rem !important;
}}

/* ── Pick-mode list rows (inline HTML) ── */
.ka-cal-pick-row {{
    border-radius: 12px; padding: 12px 14px; margin-bottom: 6px;
}}
.ka-cal-pick-date {{
    font-size: 15px; font-weight: 800; color: {p['text_primary']};
}}
.ka-cal-pick-title {{
    font-size: 14px; font-weight: 600; margin-top: 4px; color: {p['text_primary']};
}}
.ka-cal-pick-detail {{
    font-size: 13px; color: {p['text_secondary']}; margin-top: 4px;
}}

@media (max-width: 768px) {{
    .ka-cal-month-title {{ font-size: 1.1rem !important; }}
    div[data-testid="column"]:has(.ka-tt-marker),
    div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stVerticalBlock"],
    div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stButton"] button {{
        min-height: 5.5rem !important;
    }}
    div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip {{
        font-size: clamp(0.54rem, 2.35vw, 0.62rem) !important;
    }}
    /* Keep chrome button rows side-by-side (JS also pins these) */
    [data-testid="stHorizontalBlock"].ka-inline-row-forced {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
    }}
    [data-testid="stHorizontalBlock"].ka-inline-row-forced > div {{
        min-width: 0 !important;
    }}
}}
"""


def inject_calendar_theme(theme: str | None = None) -> None:
    """Inject unified calendar palette once per render."""
    st.markdown(f"<style>{build_calendar_theme_css(theme)}</style>", unsafe_allow_html=True)

