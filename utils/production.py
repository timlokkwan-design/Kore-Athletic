"""Production mode — skip sample data and dev-only UI."""
from __future__ import annotations

import os
from pathlib import Path

PRODUCTION_FLAG = Path(__file__).resolve().parent.parent / "data" / ".production"


def is_production() -> bool:
    env = os.environ.get("KORE_PRODUCTION", "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    return PRODUCTION_FLAG.exists()


def enable_production_mode() -> None:
    PRODUCTION_FLAG.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTION_FLAG.write_text("production\n", encoding="utf-8")
