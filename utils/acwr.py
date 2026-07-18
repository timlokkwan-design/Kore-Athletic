"""ACWR and Foster training load calculations (ported from V6)."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from utils.config import TRAIN_TYPES


def calc_load(train_type: str, duration: float, rpe: float, sets: int = 0, reps: int = 0, dist: int = 0) -> int:
    """Foster load with type weight and optional volume bonus."""
    weight = TRAIN_TYPES.get(train_type, {}).get("weight", 1.0)
    volume = (sets or 0) * (reps or 0) * (dist or 0)
    return int(round(duration * rpe * weight + volume * 0.01))


def _loads_for_day(logs: pd.DataFrame, athlete: str, day: date) -> float:
    ds = day.isoformat()
    day_logs = logs[(logs["student_name"] == athlete) & (logs["date"].astype(str) == ds)]
    total = 0.0
    for _, row in day_logs.iterrows():
        from utils.helpers import safe_float
        load_val = safe_float(row.get("load"), 0.0)
        if load_val > 0:
            total += load_val
        else:
            dur = safe_float(row.get("duration"), 60.0)
            rpe = safe_float(row.get("rpe"), 5.0)
            ttype = str(row.get("train_type") or "間歇跑")
            total += calc_load(ttype, dur, rpe)
    return total


def calc_acwr(logs: pd.DataFrame, athlete: str, for_date: date | None = None) -> float:
    """ACWR = 7-day acute load / (28-day chronic load / 4)."""
    ref = for_date or date.today()
    if logs.empty:
        return 0.0

    acute = sum(_loads_for_day(logs, athlete, ref - timedelta(days=i)) for i in range(7))
    chronic = sum(_loads_for_day(logs, athlete, ref - timedelta(days=i)) for i in range(28))
    chronic_avg = chronic / 4 if chronic else 1.0
    return acute / chronic_avg if chronic_avg else 0.0


def acwr_status(value: float) -> tuple[str, str]:
    """Return (label, color) for ACWR badge."""
    from utils.helpers import safe_float
    value = safe_float(value, 0.0)
    if value <= 0:
        return "-", "gray"
    if value < 0.8 or value > 1.5:
        return f"{value:.2f}", "red"
    if value > 1.3:
        return f"{value:.2f}", "yellow"
    return f"{value:.2f}", "green"


def needs_rest(acwr: float, wellness: dict | None = None) -> bool:
    """Whether athlete should rest or reduce load."""
    if acwr > 1.5 or (acwr > 0 and acwr < 0.8):
        return True
    if wellness:
        if wellness.get("sleep", 5) <= 2:
            return True
        if wellness.get("soreness", 1) >= 4:
            return True
        if wellness.get("sick"):
            return True
    return False
