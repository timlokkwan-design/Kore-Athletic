"""Upload local CSV files into Supabase (run after schema.sql and Secrets are set)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from utils.config import DATA_DIR
from utils.data_store import (
    ATTENDANCE_COLUMNS,
    COMP_COLUMNS,
    COMP_ENTRY_COLUMNS,
    INJURY_COLUMNS,
    LOG_COLUMNS,
    PENDING_COLUMNS,
    PENDING_SPECIALTY_COLUMNS,
    PERIOD_COLUMNS,
    PROGRAM_COLUMNS,
    RACE_COLUMNS,
    TEMPLATE_COLUMNS,
    USER_COLUMNS,
    VIDEO_COLUMNS,
    WELLNESS_COLUMNS,
    _ensure_cols,
    _write,
)
from utils.site_content import DEFAULT_SITE_CONTENT, SITE_CONTENT_KEY, _merge_site_content
from utils.supabase_config import is_supabase_enabled

ROOT = Path(__file__).resolve().parent
DATA = ROOT / DATA_DIR

MIGRATIONS: list[tuple[str, list[str]]] = [
    ("users.csv", USER_COLUMNS),
    ("programs.csv", PROGRAM_COLUMNS),
    ("training_logs.csv", LOG_COLUMNS),
    ("wellness.csv", WELLNESS_COLUMNS),
    ("periodization.csv", PERIOD_COLUMNS),
    ("attendance.csv", ATTENDANCE_COLUMNS),
    ("injuries.csv", INJURY_COLUMNS),
    ("competitions.csv", COMP_COLUMNS),
    ("comp_entries.csv", COMP_ENTRY_COLUMNS),
    ("videos.csv", VIDEO_COLUMNS),
    ("templates.csv", TEMPLATE_COLUMNS),
    ("pending_records.csv", PENDING_COLUMNS),
    ("pending_specialty.csv", PENDING_SPECIALTY_COLUMNS),
    ("race_records.csv", RACE_COLUMNS),
]


def _load_csv(name: str, columns: list[str]) -> pd.DataFrame:
    path = DATA / name
    if not path.exists():
        return pd.DataFrame(columns=columns)
    return _ensure_cols(pd.read_csv(path), columns)


def migrate_site_content() -> bool:
    path = DATA / "site_content.json"
    if not path.exists():
        from utils.supabase_io import write_app_setting

        write_app_setting(SITE_CONTENT_KEY, dict(DEFAULT_SITE_CONTENT))
        return True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}
    from utils.supabase_io import write_app_setting

    write_app_setting(SITE_CONTENT_KEY, _merge_site_content(data))
    return True


def migrate_csv_to_supabase() -> dict[str, int]:
    counts: dict[str, int] = {}
    for filename, columns in MIGRATIONS:
        df = _load_csv(filename, columns)
        _write(filename, df, columns)
        counts[filename] = len(df)
    migrate_site_content()
    return counts


def main() -> int:
    if not is_supabase_enabled():
        print("錯誤：未設定 Supabase。")
        print("請在本機 .streamlit/secrets.toml 或環境變數設定：")
        print("  SUPABASE_URL / SUPABASE_SERVICE_KEY")
        print("或 Streamlit Secrets：[supabase] url / service_key")
        return 1

    print("=== 匯入 CSV → Supabase ===")
    try:
        counts = migrate_csv_to_supabase()
    except Exception as exc:
        print(f"匯入失敗：{exc}")
        print("請確認已在 Supabase SQL Editor 執行 supabase/schema.sql")
        return 1

    for name, n in counts.items():
        print(f"  {name}: {n} 筆")
    print("site_content.json: 已同步")
    print("=== 完成 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
