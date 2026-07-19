"""Coach pending-approval counts — shared by sidebar, popup, and dashboard."""
from __future__ import annotations

import time

from utils.data_store import get_pending_users, load_pending_records, load_pending_specialty
from utils.session_cache import cached_value, drop_cache_keys

PENDING_LABELS = {
    "registrations": "新學員註冊",
    "scores": "比賽成績",
    "specialty": "專項更改",
}

# Re-read often so another session's submissions surface on the coach phone quickly.
_PENDING_TTL_SECONDS = 5.0
_PENDING_CACHE_KEYS = (
    "coach_pending_summary",
    "users.csv",
    "pending_records.csv",
    "pending_specialty.csv",
)


def _load_pending_summary() -> dict[str, int]:
    return {
        "registrations": len(get_pending_users()),
        "scores": len(load_pending_records()),
        "specialty": len(load_pending_specialty()),
    }


def _refresh_pending_sources_if_stale(*, force: bool = False) -> None:
    """Bypass session cache periodically so cross-user approvals appear on mobile."""
    try:
        import streamlit as st
    except Exception:
        return

    now = time.time()
    last = float(st.session_state.get("_coach_pending_refresh_at", 0) or 0)
    if force or (now - last) >= _PENDING_TTL_SECONDS:
        drop_cache_keys(*_PENDING_CACHE_KEYS)
        st.session_state["_coach_pending_refresh_at"] = now


def get_coach_pending_summary(*, force_refresh: bool = False) -> dict[str, int]:
    _refresh_pending_sources_if_stale(force=force_refresh)
    return cached_value("coach_pending_summary", _load_pending_summary)


def get_coach_pending_total(*, force_refresh: bool = False) -> int:
    return sum(get_coach_pending_summary(force_refresh=force_refresh).values())


def get_coach_pending_lines(*, force_refresh: bool = False) -> list[tuple[str, int]]:
    summary = get_coach_pending_summary(force_refresh=force_refresh)
    return [(PENDING_LABELS[key], summary[key]) for key in PENDING_LABELS if summary[key] > 0]


def pending_fingerprint(summary: dict[str, int] | None = None) -> str:
    data = summary or get_coach_pending_summary()
    return "|".join(f"{key}:{int(data.get(key, 0))}" for key in PENDING_LABELS)
