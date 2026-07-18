"""Coach pending-approval counts — shared by sidebar and dashboard."""
from __future__ import annotations

from utils.data_store import get_pending_users, load_pending_records, load_pending_specialty
from utils.session_cache import cached_value

PENDING_LABELS = {
    "registrations": "新學員註冊",
    "scores": "比賽成績",
    "specialty": "專項更改",
}


def _load_pending_summary() -> dict[str, int]:
    return {
        "registrations": len(get_pending_users()),
        "scores": len(load_pending_records()),
        "specialty": len(load_pending_specialty()),
    }


def get_coach_pending_summary() -> dict[str, int]:
    return cached_value("coach_pending_summary", _load_pending_summary)


def get_coach_pending_total() -> int:
    return sum(get_coach_pending_summary().values())


def get_coach_pending_lines() -> list[tuple[str, int]]:
    summary = get_coach_pending_summary()
    return [(PENDING_LABELS[key], summary[key]) for key in PENDING_LABELS if summary[key] > 0]
