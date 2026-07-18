"""Local CSV-based data persistence for training records."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd

from utils.config import DATA_DIR, DEFAULT_MENU, LOGS_FILE, MENUS_FILE

LOG_COLUMNS = [
    "id",
    "date",
    "student_name",
    "event",
    "rep_number",
    "target_seconds",
    "actual_seconds",
    "rpe",
    "injury_notes",
    "submitted_at",
]

MENU_COLUMNS = [
    "date",
    "event",
    "reps",
    "target_seconds",
    "description",
    "notes",
]


def _data_path(filename: str) -> Path:
    base = Path(__file__).resolve().parent.parent / DATA_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / filename


def _empty_logs() -> pd.DataFrame:
    return pd.DataFrame(columns=LOG_COLUMNS)


def _empty_menus() -> pd.DataFrame:
    return pd.DataFrame(columns=MENU_COLUMNS)


def load_logs() -> pd.DataFrame:
    path = _data_path(LOGS_FILE)
    if not path.exists():
        return _empty_logs()
    df = pd.read_csv(path)
    for col in LOG_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[LOG_COLUMNS]


def save_logs(df: pd.DataFrame) -> None:
    path = _data_path(LOGS_FILE)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def load_menus() -> pd.DataFrame:
    path = _data_path(MENUS_FILE)
    if not path.exists():
        return _empty_menus()
    df = pd.read_csv(path)
    for col in MENU_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[MENU_COLUMNS]


def save_menus(df: pd.DataFrame) -> None:
    path = _data_path(MENUS_FILE)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def get_today_menu(for_date: date | None = None) -> dict:
    """Return today's training menu; fall back to DEFAULT_MENU."""
    target_date = (for_date or date.today()).isoformat()
    menus = load_menus()

    if not menus.empty:
        match = menus[menus["date"].astype(str) == target_date]
        if not match.empty:
            row = match.iloc[0]
            return {
                "date": str(row["date"]),
                "event": str(row["event"]),
                "reps": int(row["reps"]),
                "target_seconds": float(row["target_seconds"]),
                "description": str(row["description"]),
                "notes": str(row.get("notes", "") or ""),
            }

    menu = DEFAULT_MENU.copy()
    menu["date"] = target_date
    return menu


def append_training_log(
    student_name: str,
    rep_number: int,
    actual_seconds: float,
    rpe: int,
    injury_notes: str,
    menu: dict | None = None,
) -> None:
    """Append a single rep record to the logs CSV."""
    menu = menu or get_today_menu()
    logs = load_logs()

    next_id = 1 if logs.empty else int(logs["id"].max()) + 1
    record = {
        "id": next_id,
        "date": menu["date"],
        "student_name": student_name.strip(),
        "event": menu["event"],
        "rep_number": rep_number,
        "target_seconds": menu["target_seconds"],
        "actual_seconds": actual_seconds,
        "rpe": rpe,
        "injury_notes": injury_notes,
        "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
    }
    logs = pd.concat([logs, pd.DataFrame([record])], ignore_index=True)
    save_logs(logs)


def get_logs_for_date(for_date: date | None = None) -> pd.DataFrame:
    target_date = (for_date or date.today()).isoformat()
    logs = load_logs()
    if logs.empty:
        return logs
    return logs[logs["date"].astype(str) == target_date].copy()


def get_all_logs() -> pd.DataFrame:
    return load_logs()


def init_sample_data() -> None:
    """Seed sample menu and logs if data files are empty."""
    menus = load_menus()
    if menus.empty:
        save_menus(pd.DataFrame([DEFAULT_MENU]))

    logs = load_logs()
    if logs.empty:
        sample = pd.DataFrame(
            [
                {
                    "id": 1,
                    "date": date.today().isoformat(),
                    "student_name": "王小明",
                    "event": "400m",
                    "rep_number": 1,
                    "target_seconds": 65.0,
                    "actual_seconds": 66.2,
                    "rpe": 6,
                    "injury_notes": "無不適",
                    "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                },
                {
                    "id": 2,
                    "date": date.today().isoformat(),
                    "student_name": "王小明",
                    "event": "400m",
                    "rep_number": 2,
                    "target_seconds": 65.0,
                    "actual_seconds": 65.8,
                    "rpe": 7,
                    "injury_notes": "無不適",
                    "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                },
                {
                    "id": 3,
                    "date": date.today().isoformat(),
                    "student_name": "李小華",
                    "event": "400m",
                    "rep_number": 1,
                    "target_seconds": 65.0,
                    "actual_seconds": 64.5,
                    "rpe": 5,
                    "injury_notes": "左膝",
                    "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                },
            ]
        )
        save_logs(sample)
