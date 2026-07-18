"""Unified calendar color system — grid, list, legend, compact share one palette."""
from __future__ import annotations

import streamlit as st

# ── Surfaces ──────────────────────────────────────────────────────────────
GRID_GUTTER = "#B8C4D4"
CELL_BG = "#FFFFFF"
CELL_EMPTY_BG = "#E8EDF3"
CELL_DISABLED_BG = "#DDE3EB"
LIST_CARD_BG = "#FFFFFF"
LIST_CARD_BORDER = "#C5CED8"

# ── Typography ──────────────────────────────────────────────────────────
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#374151"
TEXT_MUTED = "#5B6573"
TEXT_ON_ACCENT = "#FFFFFF"

# ── Interaction ─────────────────────────────────────────────────────────
ACCENT_TODAY = "#1565C0"
ACCENT_SELECTED = "#1565C0"
ACCENT_SELECTED_TINT = "#E8F2FC"
ACCENT_SELECTED_RING = "#1565C0"

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

# Legacy config.py aliases (cell backgrounds for list rows / helpers)
CALENDAR_BG_TRAINING = CALENDAR_TONES["training"]["bg"]
CALENDAR_BG_COMPETITION = CALENDAR_TONES["competition"]["bg"]
CALENDAR_BG_REST = CALENDAR_TONES["rest"]["bg"]
CALENDAR_BG_EMPTY = CELL_EMPTY_BG


def compact_tone_styles() -> dict[str, tuple[str, str, str]]:
    """(background, foreground, border) for square-grid calendar buttons."""
    return {
        tone: (t["bg"], t["fg"], t["border"])
        for tone, t in CALENDAR_TONES.items()
    } | {
        "attended": (
            CALENDAR_TONES["picked"]["bg"],
            CALENDAR_TONES["picked"]["fg"],
            CALENDAR_TONES["picked"]["border"],
        ),
    }


def _chip_rules(parent: str, *, compact: bool = False) -> str:
    fs = "0.56rem" if compact else "0.8rem"
    pad = "2px 4px" if compact else "6px 10px"
    radius = "4px" if compact else "7px"
    border_w = "3px" if compact else "4px"
    rules: list[str] = []
    for tone, t in CALENDAR_TONES.items():
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


def build_calendar_theme_css() -> str:
    t_train = CALENDAR_TONES["training"]
    t_comp = CALENDAR_TONES["competition"]
    t_rest = CALENDAR_TONES["rest"]

    return f"""
:root {{
    --ka-cal-grid: {GRID_GUTTER};
    --ka-cal-cell: {CELL_BG};
    --ka-cal-text: {TEXT_PRIMARY};
    --ka-cal-muted: {TEXT_MUTED};
    --ka-cal-today: {ACCENT_TODAY};
    --ka-cal-selected: {ACCENT_SELECTED_RING};
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

/* ── Month grid layout ── */
div[data-testid="stHorizontalBlock"]:has(.ka-tt-grid-marker),
div[data-testid="stHorizontalBlock"]:has(.ka-tt-hdr) {{
    display: grid !important;
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    gap: 3px !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    background: {GRID_GUTTER} !important;
    border-radius: 12px !important;
    padding: 3px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
}}
div[data-testid="stHorizontalBlock"]:has(.ka-tt-grid-marker) > div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.ka-tt-hdr) > div[data-testid="column"] {{
    padding: 0 !important; margin: 0 !important; min-width: 0 !important; flex: unset !important;
}}

div[data-testid="column"]:has(.ka-tt-marker) {{
    position: relative !important; min-height: 5rem !important;
}}
div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stVerticalBlock"] {{
    position: relative !important; min-height: 5rem !important; gap: 0 !important;
}}

div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell {{
    position: absolute; inset: 0;
    background: {CELL_BG};
    border: 1px solid #D1D9E2;
    border-radius: 8px;
    padding: 4px 3px 3px;
    display: flex; flex-direction: column; gap: 3px;
    overflow: hidden; box-sizing: border-box;
    pointer-events: none; z-index: 1;
    box-shadow: 0 1px 2px rgba(17,24,39,0.06);
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-cell.ka-tt-selected {{
    background: {ACCENT_SELECTED_TINT};
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
    font-size: 0.78rem; font-weight: 800; color: {TEXT_PRIMARY};
    line-height: 1.2; padding-left: 2px; flex-shrink: 0;
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chips {{
    display: flex; flex-direction: column; gap: 3px;
    flex: 1; min-height: 0; overflow: hidden;
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip {{
    display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
{_chip_rules('div[data-testid="column"]:has(.ka-tt-marker)', compact=True)}

div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-more {{
    font-size: 0.52rem; color: {TEXT_SECONDARY}; font-weight: 800; padding-left: 3px;
}}
div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-pick {{
    position: absolute; top: 3px; right: 3px;
    font-size: 0.58rem; font-weight: 800; color: {CALENDAR_TONES['picked']['accent']};
    background: {CALENDAR_TONES['picked']['bg']}; padding: 1px 4px; border-radius: 4px;
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
    background: {CELL_DISABLED_BG}; border-color: #C5CED8;
}}
div[data-testid="column"]:has(.ka-tt-marker[data-disabled="1"]) .ka-tt-daynum {{
    color: {TEXT_MUTED};
}}
div[data-testid="column"]:has(.ka-tt-hdr) p {{
    text-align: center !important; font-size: 0.7rem !important;
    margin: 0 !important; padding: 5px 0 !important;
    color: {TEXT_SECONDARY} !important; font-weight: 800 !important;
    background: {CELL_BG}; border-radius: 6px;
}}
div[data-testid="column"]:has(.ka-tt-empty) {{
    min-height: 5rem !important; background: {CELL_EMPTY_BG};
    border-radius: 8px; border: 1px solid #D1D9E2;
}}

/* ── List / agenda cards ── */
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) {{
    position: relative; margin-bottom: 0.45rem;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-card {{
    background: {LIST_CARD_BG};
    border: 1px solid {LIST_CARD_BORDER};
    border-radius: 12px; padding: 12px 14px;
    pointer-events: none;
    box-shadow: 0 1px 3px rgba(17,24,39,0.07);
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-card.ka-tt-list-active {{
    border-color: {ACCENT_SELECTED_RING};
    background: {ACCENT_SELECTED_TINT};
    box-shadow: inset 0 0 0 1px {ACCENT_SELECTED_RING}, 0 2px 6px rgba(21,101,192,0.12);
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-head {{
    display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-date {{
    font-size: 1.05rem; font-weight: 800; color: {TEXT_PRIMARY};
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-wd {{
    font-size: 0.85rem; color: {TEXT_SECONDARY}; font-weight: 700;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-today-tag {{
    font-size: 0.7rem; background: {ACCENT_TODAY}; color: {TEXT_ON_ACCENT};
    padding: 3px 9px; border-radius: 999px; font-weight: 800;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-chips {{
    display: flex; flex-direction: column; gap: 5px;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-chip {{
    display: block;
}}
{_chip_rules('div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap)', compact=False)}

div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-rest {{
    font-size: 0.85rem; color: {TEXT_MUTED}; font-weight: 700;
    padding: 6px 10px; background: {CELL_EMPTY_BG}; border-radius: 7px;
    border: 1px dashed #C5CED8;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) .ka-tt-list-detail {{
    font-size: 0.78rem; color: {TEXT_SECONDARY}; margin-top: 8px; font-weight: 600;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) [data-testid="stButton"] {{
    position: absolute !important; inset: 0 !important; z-index: 2 !important;
}}
div[data-testid="stVerticalBlock"]:has(.ka-tt-list-wrap) [data-testid="stButton"] button {{
    opacity: 0 !important; width: 100% !important; height: 100% !important;
    min-height: 3.75rem !important;
}}

@media (max-width: 768px) {{
    div[data-testid="column"]:has(.ka-tt-marker),
    div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stVerticalBlock"],
    div[data-testid="column"]:has(.ka-tt-marker) [data-testid="stButton"] button {{
        min-height: 5.5rem !important;
    }}
    div[data-testid="column"]:has(.ka-tt-marker) .ka-tt-chip {{
        font-size: clamp(0.54rem, 2.35vw, 0.62rem) !important;
    }}
}}
"""


def inject_calendar_theme() -> None:
    """Inject unified calendar palette once per render."""
    st.markdown(f"<style>{build_calendar_theme_css()}</style>", unsafe_allow_html=True)
