"""Bottom-right toast notifications for success / error feedback."""

from __future__ import annotations

import html
import time
from typing import Literal

import streamlit as st

ToastKind = Literal["success", "error"]

TOAST_DURATION_MS = 4500
_QUEUE_KEY = "_ka_toast_queue"
_CSS_FLAG = "_ka_toast_css"


def inject_toast_css() -> None:
    """Fixed bottom-right toast host + Streamlit toast repositioning."""
    if st.session_state.get(_CSS_FLAG):
        return
    st.session_state[_CSS_FLAG] = True
    st.markdown(
        f"""
        <style id="ka-toast-css">
        .ka-toast-host {{
          position: fixed !important;
          right: 1rem !important;
          bottom: calc(1.1rem + env(safe-area-inset-bottom, 0px)) !important;
          left: auto !important;
          top: auto !important;
          z-index: 2147483646 !important;
          display: flex !important;
          flex-direction: column !important;
          align-items: flex-end !important;
          gap: 0.5rem !important;
          max-width: min(92vw, 22rem) !important;
          pointer-events: none !important;
        }}
        .ka-toast {{
          pointer-events: auto !important;
          width: max-content !important;
          max-width: min(92vw, 22rem) !important;
          padding: 0.78rem 1rem !important;
          border-radius: 12px !important;
          font-size: 0.92rem !important;
          font-weight: 700 !important;
          line-height: 1.35 !important;
          box-shadow: 0 10px 28px rgba(0, 0, 0, 0.28) !important;
          animation: ka-toast-in 0.22s ease-out !important;
        }}
        .ka-toast-success {{
          background: #166534 !important;
          color: #ffffff !important;
          border: 1px solid #86efac !important;
        }}
        .ka-toast-error {{
          background: #991b1b !important;
          color: #ffffff !important;
          border: 1px solid #fca5a5 !important;
        }}
        @keyframes ka-toast-in {{
          from {{ opacity: 0; transform: translateY(14px); }}
          to {{ opacity: 1; transform: translateY(0); }}
        }}
        /* Native st.toast → bottom-right as backup */
        [data-testid="stToastContainer"] {{
          top: auto !important;
          bottom: calc(1.1rem + env(safe-area-inset-bottom, 0px)) !important;
          right: 1rem !important;
          left: auto !important;
          align-items: flex-end !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def queue_toast(message: str, *, kind: ToastKind = "success") -> None:
    """Queue a toast for the end of this run (survives ``st.rerun()``)."""
    text = str(message or "").strip()
    if not text:
        return
    q = st.session_state.setdefault(_QUEUE_KEY, [])
    q.append((kind, text))


def toast_success(message: str) -> None:
    queue_toast(message, kind="success")


def toast_error(message: str) -> None:
    queue_toast(message, kind="error")


def set_flash(key: str, kind: ToastKind, message: str) -> None:
    """Legacy flash tuple + toast queue (for post-rerun feedback)."""
    st.session_state[key] = (kind, str(message))
    queue_toast(message, kind=kind)


def show_flash(flash: tuple | list | None) -> None:
    """Consume a ``(kind, message)`` flash as a toast (no inline alert)."""
    if not flash:
        return
    try:
        kind, message = flash[0], flash[1]
    except (TypeError, IndexError, ValueError):
        return
    kind_s = str(kind).lower()
    if kind_s in ("success", "ok", "info"):
        toast_success(str(message))
    else:
        toast_error(str(message))


def install_feedback_toasts() -> None:
    """Also queue toasts when callers use ``st.success`` / ``st.error``."""
    if getattr(st, "_ka_toast_feedback_patched", False):
        return
    st._ka_toast_feedback_patched = True  # type: ignore[attr-defined]

    import re

    _success = st.success
    _error = st.error

    def _plain(body: object) -> str:
        text = str(body or "")
        text = re.sub(r"[*_`#]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        # Drop leading status emoji (toast adds ✓ / ✕)
        text = re.sub(r"^[✅❌⚠️✔️✖️]\s*", "", text)
        return text[:160]

    def _success_with_toast(body: object = "", *args, **kwargs):
        msg = _plain(body)
        if msg:
            toast_success(msg)
        return _success(body, *args, **kwargs)

    def _error_with_toast(body: object = "", *args, **kwargs):
        msg = _plain(body)
        if msg:
            toast_error(msg)
        return _error(body, *args, **kwargs)

    st.success = _success_with_toast  # type: ignore[assignment]
    st.error = _error_with_toast  # type: ignore[assignment]


def drain_toasts() -> None:
    """Render queued toasts once at the end of ``main()``."""
    inject_toast_css()
    items = list(st.session_state.pop(_QUEUE_KEY, []) or [])
    if not items:
        return

    # Deduplicate consecutive identical messages from double-wiring.
    deduped: list[tuple[str, str]] = []
    for kind, message in items:
        k = "success" if str(kind) == "success" else "error"
        m = str(message).strip()
        if not m:
            continue
        if deduped and deduped[-1] == (k, m):
            continue
        deduped.append((k, m))
    if not deduped:
        return

    uid = str(int(time.time() * 1000))[-8:]
    cards = []
    for i, (kind, message) in enumerate(deduped):
        icon = "✓" if kind == "success" else "✕"
        safe = html.escape(message)
        cards.append(
            f'<div class="ka-toast ka-toast-{kind}" role="status" '
            f'data-ka-toast="{uid}-{i}">{icon} {safe}</div>'
        )
    cards_html = "".join(cards)
    script = f"""
    <script>
    (function () {{
      var hostId = 'ka-toast-host';
      var host = document.getElementById(hostId);
      if (!host) {{
        host = document.createElement('div');
        host.id = hostId;
        host.className = 'ka-toast-host';
        host.setAttribute('aria-live', 'polite');
        document.body.appendChild(host);
      }}
      var wrap = document.getElementById('ka-toast-source-{uid}');
      if (!wrap) return;
      Array.prototype.slice.call(wrap.querySelectorAll('.ka-toast')).forEach(function (el) {{
        host.appendChild(el);
        setTimeout(function () {{
          el.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
          el.style.opacity = '0';
          el.style.transform = 'translateY(10px)';
          setTimeout(function () {{ el.remove(); }}, 280);
        }}, {TOAST_DURATION_MS});
      }});
      wrap.remove();
    }})();
    </script>
    """
    payload = (
        f'<div id="ka-toast-source-{uid}" style="display:none">{cards_html}</div>'
        f"{script}"
    )
    try:
        st.html(payload)
    except TypeError:
        try:
            st.html(payload, unsafe_allow_javascript=True)
        except Exception:
            st.markdown(payload, unsafe_allow_html=True)
    except Exception:
        # Fallback: native Streamlit toast (moved bottom-right by CSS)
        for kind, message in deduped:
            icon = "✅" if kind == "success" else "❌"
            try:
                st.toast(f"{message}", icon=icon, duration=5)
            except Exception:
                pass
