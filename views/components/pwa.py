"""PWA — manifest, service worker, Add to Home Screen hints."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import streamlit as st

from utils.config import APP_NAME, APP_SUBTITLE

_STATIC = Path(__file__).resolve().parent.parent.parent / ".streamlit" / "static"


def _write_png(path: Path, size: int, rgb: tuple[int, int, int] = (37, 99, 235)) -> None:
    """Minimal solid-colour PNG without external deps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return

    def _chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    row = b"\x00" + bytes(rgb) * size
    raw = row * size
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def ensure_pwa_assets() -> None:
    _write_png(_STATIC / "icon-192.png", 192)
    _write_png(_STATIC / "icon-512.png", 512, (29, 78, 216))
    manifest = _STATIC / "manifest.webmanifest"
    if not manifest.exists():
        manifest.write_text(
            f"""{{
  "name": "{APP_NAME}",
  "short_name": "{APP_NAME}",
  "description": "{APP_SUBTITLE}",
  "start_url": ".",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "orientation": "portrait-primary",
  "icons": [
    {{
      "src": "static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    }},
    {{
      "src": "static/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }}
  ]
}}""",
            encoding="utf-8",
        )
    sw = _STATIC / "sw.js"
    if not sw.exists():
        sw.write_text(
            """/* Minimal SW — enables Add to Home Screen on supported browsers */
self.addEventListener('install', (e) => self.skipWaiting());
self.addEventListener('activate', (e) => self.clients.claim());
self.addEventListener('fetch', (e) => e.respondWith(fetch(e.request)));
""",
            encoding="utf-8",
        )


def inject_pwa_head() -> None:
    ensure_pwa_assets()
    st.markdown(
        """
        <link rel="manifest" href="static/manifest.webmanifest">
        <link rel="apple-touch-icon" href="static/icon-192.png">
        <meta name="theme-color" content="#2563eb">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="KORE ATHLETIC">
        <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('static/sw.js').catch(function(){});
        }
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_pwa_install_hint() -> None:
    """Mobile hint for Safari / Chrome Add to Home Screen."""
    if st.session_state.get("pwa_hint_dismissed"):
        return
    st.markdown(
        """
        <div class="ka-pwa-hint">
            <strong>📲 加到主畫面</strong>
            <span class="ka-pwa-hint-detail">
            iPhone：Safari → 分享 → 加入主畫面 ·
            Android：Chrome → 選單 → 安裝應用程式
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("知道了", key="pwa_hint_dismiss"):
        st.session_state.pwa_hint_dismissed = True
        st.rerun()
