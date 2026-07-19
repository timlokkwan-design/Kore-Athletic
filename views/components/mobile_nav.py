"""Mobile-first navigation — Instagram-style bottom tab bars."""
from __future__ import annotations

import time

import streamlit as st


def _set_main_page(session_key: str, page: str) -> None:
    st.session_state[session_key] = page


def _set_section_with_feedback(session_key: str, section: str) -> None:
    """Switch section and mark a press flash so the tile reacts on the next paint."""
    st.session_state[session_key] = section
    st.session_state["_bottom_tab_flash"] = section
    st.session_state["_bottom_tab_flash_at"] = time.time()


def render_visitor_sidebar_nav(
    options: list[tuple[str, str]],
    session_key: str,
    default: str,
) -> str:
    """Visitor navigation inside sidebar (replaces main-area top buttons)."""
    values = [val for _, val in options]
    if session_key not in st.session_state or st.session_state[session_key] not in values:
        st.session_state[session_key] = default

    st.markdown("<p class='ka-nav-label'>瀏覽</p>", unsafe_allow_html=True)
    current = st.session_state[session_key]
    for label, val in options:
        st.button(
            label,
            key=f"vis_nav_{val}",
            use_container_width=True,
            type="primary" if current == val else "secondary",
            on_click=_set_main_page,
            args=(session_key, val),
        )
    return st.session_state[session_key]


def _pin_innermost_dock_host() -> None:
    """Pin only a small dock-only block. Never fix the page root (locks scroll)."""
    try:
        st.html(
            """
            <script>
            (function () {
              function unlockScroll() {
                var unlock = [
                  document.documentElement,
                  document.body,
                  document.querySelector('.stApp'),
                  document.querySelector('[data-testid="stAppViewContainer"]'),
                  document.querySelector('section.main'),
                  document.querySelector('section.main .block-container')
                ];
                unlock.forEach(function (el) {
                  if (!el || !el.style) return;
                  el.style.setProperty('overflow', 'visible', 'important');
                  el.style.setProperty('overflow-y', 'auto', 'important');
                  el.style.setProperty('height', 'auto', 'important');
                  el.style.setProperty('max-height', 'none', 'important');
                  if (el.classList && el.classList.contains('ka-bottom-dock-host')) return;
                  // Never leave the page shell position:fixed
                  if (el.style.position === 'fixed') {
                    el.style.setProperty('position', 'relative', 'important');
                  }
                });
                // Strip mistaken host class from large blocks
                document.querySelectorAll('.ka-bottom-dock-host').forEach(function (el) {
                  var h = el.getBoundingClientRect().height;
                  var bad = h > 180
                    || el.querySelector('[data-testid="stExpander"]')
                    || el.querySelector('[data-testid="stDataFrame"]')
                    || el.querySelector('section.main')
                    || (el.querySelectorAll('button').length > 8);
                  if (bad) el.classList.remove('ka-bottom-dock-host');
                });
              }

              function pinDock() {
                unlockScroll();
                document.querySelectorAll('.ka-bottom-dock-host').forEach(function (el) {
                  el.classList.remove('ka-bottom-dock-host');
                });
                var markers = document.querySelectorAll('.ka-bottom-tabbar-marker');
                markers.forEach(function (marker) {
                  var node = marker.parentElement;
                  var deepest = null;
                  while (node && node !== document.body) {
                    if (node.getAttribute && node.getAttribute('data-testid') === 'stVerticalBlock') {
                      deepest = node;
                      break;
                    }
                    node = node.parentElement;
                  }
                  if (!deepest) return;
                  var h = deepest.getBoundingClientRect().height;
                  var btns = deepest.querySelectorAll('button').length;
                  var bad = h > 180
                    || deepest.querySelector('[data-testid="stExpander"]')
                    || deepest.querySelector('[data-testid="stDataFrame"]')
                    || btns < 2
                    || btns > 8;
                  if (bad) return;
                  deepest.classList.add('ka-bottom-dock-host');
                });
                unlockScroll();
              }
              pinDock();
              setTimeout(pinDock, 50);
              setTimeout(pinDock, 200);
              setTimeout(pinDock, 500);
            })();
            </script>
            """,
            unsafe_allow_javascript=True,
        )
    except TypeError:
        pass
    except Exception:
        pass


def _render_bottom_tabbar(
    *,
    marker_class: str,
    items: list[tuple[str, str, str]],
    current_section: str,
    session_key: str,
    key_prefix: str,
    active_aliases: dict[str, set[str]] | None = None,
) -> None:
    """Fixed bottom tab bar — single horizontal row on mobile (Instagram-style).

    items: (icon, short_label, section_value)
    active_aliases: map dock section → other sections that should also light up the tile
    """
    st.markdown(
        """
        <style>
        /* Page must always scroll; only .ka-bottom-dock-host may be fixed */
        html, body, .stApp,
        [data-testid="stAppViewContainer"],
        section.main,
        section.main .block-container {
          overflow-x: hidden !important;
          overflow-y: auto !important;
          height: auto !important;
          max-height: none !important;
        }
        section.main div[data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host) {
          position: static !important;
          height: auto !important;
          max-height: none !important;
          overflow: visible !important;
        }
        .ka-bottom-dock-host [data-testid="stHorizontalBlock"] {
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: nowrap !important;
          width: 100% !important;
          gap: 0.18rem !important;
        }
        .ka-bottom-dock-host [data-testid="stHorizontalBlock"] > div,
        .ka-bottom-dock-host [data-testid="column"],
        .ka-bottom-dock-host [data-testid="stColumn"] {
          flex: 1 1 0 !important;
          min-width: 0 !important;
          width: auto !important;
          max-width: none !important;
        }
        @keyframes ka-tab-pop {
          0%   { transform: scale(0.86); filter: brightness(1.15); }
          55%  { transform: scale(1.06); }
          100% { transform: scale(1); }
        }
        .ka-bottom-dock-host button[kind="primary"],
        .ka-bottom-dock-host button[data-testid="baseButton-primary"] {
          animation: ka-tab-pop 0.3s ease !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    flash = st.session_state.get("_bottom_tab_flash")

    with st.container():
        st.markdown(f'<div class="{marker_class}" aria-hidden="true"></div>', unsafe_allow_html=True)
        cols = st.columns(len(items), gap="small")
        aliases = active_aliases or {}
        for col, (icon, label, section) in zip(cols, items):
            related = aliases.get(section, set())
            is_active = current_section == section or current_section in related
            btn_label = f"{icon}\n{label}"
            with col:
                st.button(
                    btn_label,
                    key=f"{key_prefix}_{section}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_set_section_with_feedback,
                    args=(session_key, section),
                )

    _pin_innermost_dock_host()

    if flash is not None:
        st.session_state.pop("_bottom_tab_flash", None)


def render_student_quick_dock(current_section: str) -> None:
    """Student Instagram-style bottom tabs: 課表 / 簽到 / 日誌 / 比賽."""
    _render_bottom_tabbar(
        marker_class="ka-bottom-tabbar-marker ka-student-dock-marker",
        items=[
            ("📅", "課表", "訓練時間表"),
            ("✅", "簽到", "出席"),
            ("📝", "日誌", "訓練日誌"),
            ("🏅", "比賽", "比賽報名"),
        ],
        current_section=current_section,
        session_key="student_section",
        key_prefix="stu_dock",
        active_aliases={"比賽報名": {"賽事時間表", "提交比賽成績"}},
    )


def render_coach_bottom_dock(current_section: str) -> None:
    """Coach Instagram-style bottom tabs: 總覽 / 課表 / 出席 / 隊伍 / 比賽."""
    _render_bottom_tabbar(
        marker_class="ka-bottom-tabbar-marker ka-coach-dock-marker",
        items=[
            ("🏠", "總覽", "總覽"),
            ("📅", "課表", "訓練時間表"),
            ("✅", "出席", "出席表"),
            ("👥", "隊伍", "隊伍管理"),
            ("🏅", "比賽", "比賽報名表"),
        ],
        current_section=current_section,
        session_key="coach_section",
        key_prefix="coach_dock",
        active_aliases={"比賽報名表": {"賽事時間表", "比賽管理"}, "訓練時間表": {"設定課表"}},
    )
