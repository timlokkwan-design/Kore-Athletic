"""Mobile-first navigation — Instagram-style bottom / top tab bars."""
from __future__ import annotations

import time

import streamlit as st

# Sticky top sub-tab clusters: any category with 2+ sections.
# Each item: (icon, short_label, section_value)
COACH_TOP_CLUSTERS: list[tuple[str, list[tuple[str, str, str]]]] = [
    (
        "train",
        [
            ("👀", "檢視", "課表檢視"),
            ("📅", "時間", "訓練時間表"),
            ("✏️", "設定", "設定課表"),
        ],
    ),
    (
        "team",
        [
            ("✅", "出席", "出席表"),
            ("❤️", "健康", "ACWR/健康"),
            ("👥", "隊伍", "隊伍管理"),
        ],
    ),
    (
        "comp",
        [
            ("📅", "時間表", "賽事時間表"),
            ("📋", "報名表", "比賽報名表"),
            ("⚙️", "管理", "比賽管理"),
        ],
    ),
    (
        "comms",
        [
            ("📢", "消息", "最新消息"),
            ("🎬", "影片", "影片分析"),
            ("💬", "家長", "家長溝通"),
        ],
    ),
]

STUDENT_TOP_CLUSTERS: list[tuple[str, list[tuple[str, str, str]]]] = [
    (
        "daily",
        [
            ("📅", "課表", "訓練時間表"),
            ("📢", "消息", "最新消息"),
            ("📝", "日誌", "訓練日誌"),
            ("🛏️", "健康", "健康問卷"),
            ("✅", "出席", "出席"),
        ],
    ),
    (
        "comp",
        [
            ("📅", "時間表", "賽事時間表"),
            ("📝", "報名", "比賽報名"),
            ("🏁", "成績", "提交比賽成績"),
        ],
    ),
]

COACH_COMP_SECTIONS = tuple(s for _, _, s in COACH_TOP_CLUSTERS[2][1])
STUDENT_COMP_SECTIONS = tuple(s for _, _, s in STUDENT_TOP_CLUSTERS[1][1])
COACH_TRAIN_SECTIONS = tuple(s for _, _, s in COACH_TOP_CLUSTERS[0][1])


def _cluster_for_section(
    clusters: list[tuple[str, list[tuple[str, str, str]]]],
    section: str,
) -> tuple[str, list[tuple[str, str, str]]] | None:
    for key, items in clusters:
        if section in {s for _, _, s in items}:
            return key, items
    return None


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


def _find_innermost_vertical_block_js() -> str:
    """Shared JS: find dock/subtab host + force ONLY that row (never page-wide)."""
    return """
              function findHost(marker) {
                var node = marker.parentElement;
                while (node && node !== document.body) {
                  if (node.getAttribute && node.getAttribute('data-testid') === 'stVerticalBlock') {
                    return node;
                  }
                  node = node.parentElement;
                }
                return null;
              }
              function directRows(host) {
                var out = [];
                if (!host) return out;
                host.querySelectorAll('[data-testid="stHorizontalBlock"]').forEach(function (row) {
                  var p = row.parentElement;
                  var nested = false;
                  while (p && p !== host) {
                    if (p.getAttribute && p.getAttribute('data-testid') === 'stVerticalBlock') {
                      nested = true;
                      break;
                    }
                    p = p.parentElement;
                  }
                  if (!nested) out.push(row);
                });
                return out;
              }
              function forceRowOn(row) {
                if (!row) return;
                row.style.setProperty('display', 'flex', 'important');
                row.style.setProperty('flex-direction', 'row', 'important');
                row.style.setProperty('flex-wrap', 'nowrap', 'important');
                row.style.setProperty('width', '100%', 'important');
                row.style.setProperty('align-items', 'stretch', 'important');
                Array.prototype.forEach.call(row.children, function (col) {
                  col.style.setProperty('flex', '1 1 0', 'important');
                  col.style.setProperty('min-width', '0', 'important');
                  col.style.setProperty('max-width', 'none', 'important');
                  col.style.setProperty('width', 'auto', 'important');
                });
              }
              function clearRowInline(row) {
                if (!row || !row.style) return;
                ['display','flex-direction','flex-wrap','width','align-items'].forEach(function (p) {
                  row.style.removeProperty(p);
                });
                Array.prototype.forEach.call(row.children || [], function (col) {
                  if (!col.style) return;
                  ['flex','min-width','max-width','width'].forEach(function (p) {
                    col.style.removeProperty(p);
                  });
                });
              }
              function scrubLeakedRowStyles() {
                document.querySelectorAll('[data-testid="stHorizontalBlock"]').forEach(function (row) {
                  if (row.closest('.ka-bottom-dock-host') || row.closest('.ka-top-subtab-host')) return;
                  clearRowInline(row);
                });
              }
              function isWrongHost(el, minBtns, maxBtns) {
                if (!el) return true;
                var btns = el.querySelectorAll('button').length;
                if (btns < minBtns || btns > maxBtns) return true;
                if (el.querySelector('iframe') || el.querySelector('.fc')) return true;
                if (el.querySelector('[data-testid="stExpander"]')) return true;
                if (el.querySelector('[data-testid="stDataFrame"]')) return true;
                if (el.querySelector('section.main')) return true;
                if (el.querySelector('.ka-cal-month-nav-marker')) return true;
                if (el.querySelector('.ka-cal-view-marker')) return true;
                if (el.querySelector('.ka-cal-shell-marker')) return true;
                var rows = directRows(el);
                if (rows.length !== 1) return true;
                var h = el.getBoundingClientRect().height;
                if (h > 200) return true;
                return false;
              }
    """


def _pin_innermost_dock_host() -> None:
    """Pin only small dock/subtab blocks. Never rewrite other page columns."""
    try:
        st.html(
            f"""
            <script>
            (function () {{
              {_find_innermost_vertical_block_js()}
              function unlockScroll() {{
                var unlock = [
                  document.documentElement,
                  document.body,
                  document.querySelector('.stApp'),
                  document.querySelector('[data-testid="stAppViewContainer"]'),
                  document.querySelector('section.main'),
                  document.querySelector('section.main .block-container')
                ];
                unlock.forEach(function (el) {{
                  if (!el || !el.style) return;
                  el.style.setProperty('overflow', 'visible', 'important');
                  el.style.setProperty('overflow-y', 'auto', 'important');
                  el.style.setProperty('height', 'auto', 'important');
                  el.style.setProperty('max-height', 'none', 'important');
                  if (el.classList && (
                    el.classList.contains('ka-bottom-dock-host')
                    || el.classList.contains('ka-top-subtab-host')
                  )) return;
                  if (el.style.position === 'fixed') {{
                    el.style.setProperty('position', 'relative', 'important');
                  }}
                }});
              }}

              function headerBottom() {{
                var header = document.querySelector('[data-testid="stHeader"]')
                  || document.querySelector('header');
                if (!header) return 0;
                return Math.max(0, header.getBoundingClientRect().bottom);
              }}

              function placeTopHost() {{
                var host = document.querySelector('.ka-top-subtab-host');
                var bc = document.querySelector('section.main .block-container');
                if (!host) {{
                  document.documentElement.style.removeProperty('--ka-top-pad');
                  if (bc) bc.classList.remove('ka-has-top-subtabs');
                  return;
                }}
                var rows = directRows(host);
                if (rows[0]) forceRowOn(rows[0]);
                var top = Math.max(headerBottom(), 2.75 * 16);
                host.style.setProperty('top', top + 'px', 'important');
                host.style.setProperty('position', 'fixed', 'important');
                host.style.setProperty('left', '0', 'important');
                host.style.setProperty('right', '0', 'important');
                host.style.setProperty('z-index', '2147482800', 'important');
                var h = host.getBoundingClientRect().height || 56;
                document.documentElement.style.setProperty('--ka-top-pad', (top + h + 10) + 'px');
                if (bc) bc.classList.add('ka-has-top-subtabs');
              }}

              function pinByMarker(markerSel, hostClass) {{
                document.querySelectorAll('.' + hostClass).forEach(function (el) {{
                  el.classList.remove(hostClass);
                }});
                document.querySelectorAll(markerSel).forEach(function (marker) {{
                  var host = findHost(marker);
                  if (!host) return;
                  var rows = directRows(host);
                  if (rows.length === 1) forceRowOn(rows[0]);
                  if (isWrongHost(host, 2, 10)) return;
                  host.classList.add(hostClass);
                  if (rows[0]) {{
                    forceRowOn(rows[0]);
                    // Bottom dock: last column is Manage-FAB spacer
                    if (hostClass === 'ka-bottom-dock-host' && rows[0].children.length > 2) {{
                      var last = rows[0].lastElementChild;
                      if (last && last.style) {{
                        last.style.setProperty('flex', '0 0 4.75rem', 'important');
                        last.style.setProperty('max-width', '4.75rem', 'important');
                        last.style.setProperty('min-width', '4.5rem', 'important');
                      }}
                    }}
                  }}
                }});
              }}

              function pinAll() {{
                unlockScroll();
                pinByMarker('.ka-bottom-tabbar-marker', 'ka-bottom-dock-host');
                pinByMarker('.ka-top-subtab-marker', 'ka-top-subtab-host');
                // Strip any leftover inline flex hacks from calendar / content rows
                scrubLeakedRowStyles();
                // Re-apply only on real hosts after scrub
                document.querySelectorAll('.ka-bottom-dock-host, .ka-top-subtab-host').forEach(function (host) {{
                  var rows = directRows(host);
                  if (rows[0]) forceRowOn(rows[0]);
                }});
                placeTopHost();
                unlockScroll();
              }}
              pinAll();
              setTimeout(pinAll, 80);
              setTimeout(pinAll, 400);
            }})();
            </script>
            """,
            unsafe_allow_javascript=True,
        )
    except TypeError:
        pass
    except Exception:
        pass


def render_sidebar_menu_button() -> None:
    """Always-visible control to open the left sidebar (coach + student + visitor)."""
    st.markdown(
        """
        <style>
        /* Keep Streamlit sidebar expand controls visible & tappable */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stExpandSidebarButton"] {
          display: flex !important;
          visibility: visible !important;
          opacity: 1 !important;
          pointer-events: auto !important;
          z-index: 2147483646 !important;
        }
        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button,
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stExpandSidebarButton"] button {
          min-width: 2.75rem !important;
          min-height: 2.75rem !important;
          pointer-events: auto !important;
        }
        .ka-sidebar-open-btn {
          position: fixed !important;
          top: 0.55rem !important;
          left: 0.45rem !important;
          z-index: 2147483647 !important;
          min-height: 2.6rem !important;
          padding: 0.35rem 0.75rem !important;
          border-radius: 10px !important;
          border: 1px solid #cbd5e1 !important;
          background: #ffffff !important;
          color: #0f172a !important;
          font-size: 0.85rem !important;
          font-weight: 700 !important;
          box-shadow: 0 4px 14px rgba(15, 23, 42, 0.14) !important;
          cursor: pointer !important;
          pointer-events: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    try:
        st.html(
            """
            <button type="button" class="ka-sidebar-open-btn" id="ka-open-sidebar">☰ 選單</button>
            <script>
            (function () {
              function findSidebarToggle() {
                var sels = [
                  '[data-testid="stSidebarCollapsedControl"] button',
                  '[data-testid="collapsedControl"] button',
                  '[data-testid="stSidebarCollapseButton"] button',
                  '[data-testid="stExpandSidebarButton"] button',
                  '[data-testid="stSidebarCollapsedControl"]',
                  '[data-testid="collapsedControl"]',
                  '[data-testid="stSidebarCollapseButton"]',
                  'button[kind="headerNoPadding"]',
                  'button[kind="header"]'
                ];
                for (var i = 0; i < sels.length; i++) {
                  var el = document.querySelector(sels[i]);
                  if (el) return el;
                }
                return null;
              }
              function openSidebar() {
                var el = findSidebarToggle();
                if (!el) return false;
                el.click();
                return true;
              }
              function bind() {
                var btn = document.getElementById('ka-open-sidebar');
                if (!btn || btn.dataset.bound === '1') return;
                btn.dataset.bound = '1';
                btn.addEventListener('click', function (e) {
                  e.preventDefault();
                  e.stopPropagation();
                  if (!openSidebar()) {
                    // Retry shortly — Streamlit header may still be mounting
                    setTimeout(openSidebar, 100);
                    setTimeout(openSidebar, 400);
                  }
                });
              }
              bind();
              setTimeout(bind, 200);
              setTimeout(bind, 800);
            })();
            </script>
            """,
            unsafe_allow_javascript=True,
        )
    except TypeError:
        st.markdown(
            '<button type="button" class="ka-sidebar-open-btn" id="ka-open-sidebar">☰ 選單</button>',
            unsafe_allow_html=True,
        )
    except Exception:
        pass


def _render_top_subtabbar(
    *,
    items: list[tuple[str, str, str]],
    current_section: str,
    session_key: str,
    key_prefix: str,
) -> None:
    """Fixed top sub-tabs — same horizontal tile style as the bottom dock.

    items: (icon, short_label, section_value)
    Pinned with position:fixed (sticky fails inside Streamlit layout).
    """
    if current_section not in {s for _, _, s in items}:
        return

    st.markdown(
        """
        <style>
        section.main div[data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host) {
          position: static !important;
          height: auto !important;
          max-height: none !important;
          overflow: visible !important;
        }
        .ka-top-subtab-host [data-testid="stHorizontalBlock"] {
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: nowrap !important;
          width: 100% !important;
          gap: 0.18rem !important;
        }
        .ka-top-subtab-host [data-testid="stHorizontalBlock"] > div,
        .ka-top-subtab-host [data-testid="column"],
        .ka-top-subtab-host [data-testid="stColumn"] {
          flex: 1 1 0 !important;
          min-width: 0 !important;
          width: auto !important;
          max-width: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=False):
        st.markdown(
            '<div class="ka-top-subtab-marker" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(len(items), gap="small")
        for col, (icon, label, section) in zip(cols, items):
            is_active = current_section == section
            with col:
                st.button(
                    f"{icon}\n{label}",
                    key=f"{key_prefix}_{section}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_set_section_with_feedback,
                    args=(session_key, section),
                )

    # Pin runs once from bottom dock (avoids double JS + layout thrash).


def render_coach_top_subtabs(current_section: str) -> None:
    """Sticky top sub-tabs for every multi-section coach category."""
    matched = _cluster_for_section(COACH_TOP_CLUSTERS, current_section)
    if not matched:
        return
    key, items = matched
    _render_top_subtabbar(
        items=items,
        current_section=current_section,
        session_key="coach_section",
        key_prefix=f"coach_top_{key}",
    )


def render_student_top_subtabs(current_section: str) -> None:
    """Sticky top sub-tabs for every multi-section student category."""
    matched = _cluster_for_section(STUDENT_TOP_CLUSTERS, current_section)
    if not matched:
        return
    key, items = matched
    _render_top_subtabbar(
        items=items,
        current_section=current_section,
        session_key="student_section",
        key_prefix=f"stu_top_{key}",
    )


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
        section.main div[data-testid="stVerticalBlock"]:not(.ka-bottom-dock-host):not(.ka-top-subtab-host) {
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
        # Extra trailing column = clearance for Streamlit Cloud Manage crown FAB
        cols = st.columns(len(items) + 1, gap="small")
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
        # Last column intentionally empty — keeps 比賽／隊伍 clear of Manage FAB
        with cols[-1]:
            st.markdown(
                '<div class="ka-dock-fab-spacer" aria-hidden="true"></div>',
                unsafe_allow_html=True,
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
        active_aliases={
            "比賽報名": {"賽事時間表", "提交比賽成績"},
            "訓練時間表": {"最新消息", "健康問卷"},
        },
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
        active_aliases={
            "比賽報名表": {"賽事時間表", "比賽管理"},
            "訓練時間表": {"設定課表", "課表檢視"},
            "出席表": {"ACWR/健康"},
            # 分析與溝通 has no bottom tile; top sub-tabs cover it via sidebar.
        },
    )
