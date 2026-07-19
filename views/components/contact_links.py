"""Public contact — Instagram / in-app only (no public phone)."""
from __future__ import annotations

import streamlit as st

from utils.site_content import load_site_content


def instagram_url(handle: str) -> str:
    h = str(handle or "").strip().lstrip("@")
    if not h:
        return ""
    return f"https://instagram.com/{h}"


def render_instagram_button(
    label: str = "📷 Instagram 聯絡本會",
    *,
    key: str = "ig_contact",
) -> None:
    content = load_site_content()
    url = instagram_url(content.get("instagram_handle", ""))
    if url:
        st.link_button(label, url, use_container_width=True)
    else:
        st.caption("Instagram 帳號尚未設定，請教練在「網站內容」更新。")


def render_contact_block() -> None:
    content = load_site_content()
    st.write(content.get("contact_info", ""))
    render_instagram_button()
