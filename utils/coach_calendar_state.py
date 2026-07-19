"""Shared coach calendar cursor — 設定課表 ↔ 訓練時間表.

Both pages read/write the same year, month, and selected date so navigating
one calendar keeps the other in sync when the coach switches sections.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

YEAR_KEY = "cal_year"
MONTH_KEY = "cal_month"
DATE_KEY = "coach_cal"

# Legacy keys from 訓練時間表 before sync
_LEGACY_YEAR = "sched_cal_year"
_LEGACY_MONTH = "sched_cal_month"
_LEGACY_DATE = "sched_cal"


def ensure_coach_calendar_state() -> None:
    """Initialize / migrate shared calendar state once per session touch."""
    today = date.today()

    if YEAR_KEY not in st.session_state and _LEGACY_YEAR in st.session_state:
        st.session_state[YEAR_KEY] = int(st.session_state[_LEGACY_YEAR])
        st.session_state[MONTH_KEY] = int(st.session_state.get(_LEGACY_MONTH, today.month))
    if YEAR_KEY not in st.session_state:
        st.session_state[YEAR_KEY] = today.year
        st.session_state[MONTH_KEY] = today.month

    if DATE_KEY not in st.session_state and _LEGACY_DATE in st.session_state:
        st.session_state[DATE_KEY] = str(st.session_state[_LEGACY_DATE])
    if DATE_KEY not in st.session_state:
        st.session_state[DATE_KEY] = today.isoformat()

    # Keep legacy aliases mirrored so older widgets / flashes stay consistent
    st.session_state[_LEGACY_YEAR] = int(st.session_state[YEAR_KEY])
    st.session_state[_LEGACY_MONTH] = int(st.session_state[MONTH_KEY])
    st.session_state[_LEGACY_DATE] = str(st.session_state[DATE_KEY])


def set_coach_calendar_month(year: int, month: int) -> None:
    ensure_coach_calendar_state()
    st.session_state[YEAR_KEY] = int(year)
    st.session_state[MONTH_KEY] = int(month)
    st.session_state[_LEGACY_YEAR] = int(year)
    st.session_state[_LEGACY_MONTH] = int(month)


def set_coach_calendar_date(ds: str) -> None:
    ensure_coach_calendar_state()
    text = str(ds).strip()[:10]
    st.session_state[DATE_KEY] = text
    st.session_state[_LEGACY_DATE] = text
    try:
        d = date.fromisoformat(text)
        set_coach_calendar_month(d.year, d.month)
    except ValueError:
        pass


def get_coach_calendar_year_month() -> tuple[int, int]:
    ensure_coach_calendar_state()
    return int(st.session_state[YEAR_KEY]), int(st.session_state[MONTH_KEY])


def get_coach_calendar_date() -> str:
    ensure_coach_calendar_state()
    return str(st.session_state[DATE_KEY])
