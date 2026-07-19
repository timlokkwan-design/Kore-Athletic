"""Shared browser cookie/localStorage helpers for Streamlit (top window)."""

from __future__ import annotations

import json


def browser_storage_js() -> str:
    """Resolve top-level document + localStorage (works on Streamlit Cloud / PWA)."""
    return """
    function _kaStore() {
        const tries = [];
        try { if (window.top) tries.push(window.top); } catch (e) {}
        try { if (window.parent && window.parent !== window) tries.push(window.parent); } catch (e) {}
        tries.push(window);
        for (const w of tries) {
            try {
                return { doc: w.document, ls: w.localStorage, loc: w.location };
            } catch (e) {}
        }
        return { doc: document, ls: localStorage, loc: window.location };
    }
    const _ka = _kaStore();
    const _kaDoc = _ka.doc;
    const _kaLs = _ka.ls;
    const _kaSecure = (_ka.loc && _ka.loc.protocol === 'https:') ? '; Secure' : '';
    """


def set_browser_cookie_js(cookie_name: str, token: str, max_age: int) -> str:
    return f"""
    {browser_storage_js()}
    _kaDoc.cookie = {json.dumps(cookie_name)} + "=" + encodeURIComponent({json.dumps(token)})
        + "; path=/; max-age={max_age}; SameSite=Lax" + _kaSecure;
    """


def clear_browser_cookie_js(cookie_name: str) -> str:
    return f"""
    {browser_storage_js()}
    _kaDoc.cookie = {json.dumps(cookie_name)} + "=; path=/; max-age=0; SameSite=Lax" + _kaSecure;
    """
