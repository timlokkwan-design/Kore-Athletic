"""Streamlit Community Cloud helpers."""
from __future__ import annotations

import os


def is_streamlit_cloud() -> bool:
    return os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud"


def default_coach_credentials() -> tuple[str, str]:
    username, password = "ktll", "170330"
    if not is_streamlit_cloud():
        return username, password
    try:
        import streamlit as st

        coach = st.secrets.get("coach", {})
        username = str(coach.get("username") or username).strip() or username
        password = str(coach.get("password") or password).strip() or password
    except Exception:
        pass
    return username, password
