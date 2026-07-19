"""Read/write pandas tables via Supabase PostgreSQL."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from utils.supabase_config import get_supabase_client

logger = logging.getLogger(__name__)

CSV_TO_TABLE: dict[str, str] = {
    "programs.csv": "ka_programs",
    "users.csv": "ka_users",
    "training_logs.csv": "ka_training_logs",
    "wellness.csv": "ka_wellness",
    "periodization.csv": "ka_periodization",
    "attendance.csv": "ka_attendance",
    "injuries.csv": "ka_injuries",
    "competitions.csv": "ka_competitions",
    "comp_entries.csv": "ka_comp_entries",
    "videos.csv": "ka_videos",
    "templates.csv": "ka_templates",
    "pending_records.csv": "ka_pending_records",
    "pending_specialty.csv": "ka_pending_specialty",
    "race_records.csv": "ka_race_records",
    "student_goals.csv": "ka_student_goals",
    "announcements.csv": "ka_announcements",
}

INTERNAL_COLUMNS = {"row_id"}
INSERT_BATCH = 200

# Tables added after older deployments — missing ones must not crash the student home page.
_MISSING_TABLE_WARNED: set[str] = set()


def _api_error_fields(exc: BaseException) -> tuple[str, str]:
    code = str(getattr(exc, "code", "") or "")
    message = str(getattr(exc, "message", "") or exc)
    return code, message


def is_missing_relation_error(exc: BaseException) -> bool:
    """True when PostgREST/Postgres says the table is absent from the schema cache."""
    code, message = _api_error_fields(exc)
    text = f"{code} {message}".lower()
    return (
        code in {"PGRST205", "42P01"}
        or "could not find the table" in text
        or "does not exist" in text
        or "schema cache" in text
    )


def _warn_missing_table(table: str, filename: str, exc: BaseException) -> None:
    if table in _MISSING_TABLE_WARNED:
        return
    _MISSING_TABLE_WARNED.add(table)
    code, message = _api_error_fields(exc)
    logger.warning(
        "Supabase table %s (for %s) is missing (%s: %s). "
        "Returning empty data. Run supabase/schema_patch_v202.sql in the SQL Editor.",
        table,
        filename,
        code or "?",
        message,
    )


def _ensure_cols(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]


def _table_for_file(filename: str) -> str:
    table = CSV_TO_TABLE.get(filename)
    if not table:
        raise KeyError(f"未設定 Supabase 資料表對應：{filename}")
    return table


def _df_to_records(df: pd.DataFrame, columns: list[str]) -> list[dict]:
    clean = _ensure_cols(df.copy(), columns)
    clean = clean.where(pd.notna(clean), None)
    records: list[dict] = []
    for row in clean.to_dict(orient="records"):
        item = {col: (None if row.get(col) is None else row.get(col)) for col in columns}
        records.append(item)
    return records


def _sanitize_records(records: list[dict]) -> list[dict]:
    out = []
    for row in records:
        item: dict = {}
        for key, value in row.items():
            if value is None or (isinstance(value, float) and pd.isna(value)):
                item[key] = None
            else:
                item[key] = str(value)
        out.append(item)
    return out


def read_csv_table(filename: str, columns: list[str]) -> pd.DataFrame:
    table = _table_for_file(filename)
    client = get_supabase_client()
    try:
        resp = client.table(table).select("*").execute()
    except Exception as exc:
        # Missing new tables (e.g. ka_announcements) must not take down student pages.
        if is_missing_relation_error(exc):
            _warn_missing_table(table, filename, exc)
            return pd.DataFrame(columns=columns)
        raise
    rows = resp.data or []
    if not rows:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(rows)
    drop = [c for c in INTERNAL_COLUMNS if c in df.columns and c not in columns]
    if drop:
        df = df.drop(columns=drop)
    return _ensure_cols(df, columns)


def write_csv_table(filename: str, df: pd.DataFrame, columns: list[str]) -> None:
    """Replace-table write. For users.csv prefer protected_save_users / upsert_users_table."""
    if filename == "users.csv":
        # Safety net: never clear-replace users through the generic path.
        from utils.user_protection import protected_save_users

        protected_save_users(df, columns, reason="write_csv_table-users")
        return
    write_csv_table_replace(filename, df, columns)


def write_csv_table_replace(filename: str, df: pd.DataFrame, columns: list[str]) -> None:
    """Raw clear-then-insert (used after merge-protect for users, or for other tables)."""
    from utils.supabase_config import is_supabase_enabled

    if not is_supabase_enabled():
        from utils.config import DATA_DIR

        root = Path(__file__).resolve().parent.parent / DATA_DIR
        root.mkdir(parents=True, exist_ok=True)
        _ensure_cols(df.copy(), columns).to_csv(root / filename, index=False, encoding="utf-8-sig")
        return

    table = _table_for_file(filename)
    client = get_supabase_client()
    try:
        client.rpc("ka_clear_table", {"tname": table}).execute()
        records = _sanitize_records(_df_to_records(df, columns))
        if not records:
            return
        for i in range(0, len(records), INSERT_BATCH):
            client.table(table).insert(records[i : i + INSERT_BATCH]).execute()
    except Exception as exc:
        if is_missing_relation_error(exc):
            raise RuntimeError(
                f"Supabase 未有資料表 `{table}`（對應 {filename}）。"
                f"請到 Supabase → SQL Editor 執行 supabase/schema_patch_v202.sql 後再試。"
            ) from exc
        raise


def upsert_users_table(df: pd.DataFrame, columns: list[str]) -> None:
    """Upsert ka_users by username when a unique constraint exists.

    Falls back to caller if PostgREST rejects on_conflict.
    """
    table = _table_for_file("users.csv")
    client = get_supabase_client()
    records = _sanitize_records(_df_to_records(df, columns))
    if not records:
        return
    for i in range(0, len(records), INSERT_BATCH):
        chunk = records[i : i + INSERT_BATCH]
        client.table(table).upsert(chunk, on_conflict="username").execute()


def delete_users_by_username(usernames: list[str]) -> int:
    """Hard-delete specific usernames only (test-account cleanup)."""
    names = [str(u).strip() for u in usernames if str(u).strip()]
    if not names:
        return 0
    from utils.supabase_config import is_supabase_enabled

    if not is_supabase_enabled():
        return 0
    table = _table_for_file("users.csv")
    client = get_supabase_client()
    client.table(table).delete().in_("username", names).execute()
    return len(names)

def read_app_setting(key: str) -> dict | None:
    client = get_supabase_client()
    resp = client.table("ka_app_settings").select("value").eq("key", key).limit(1).execute()
    rows = resp.data or []
    if not rows:
        return None
    value = rows[0].get("value")
    return value if isinstance(value, dict) else None


def write_app_setting(key: str, value: dict) -> None:
    client = get_supabase_client()
    client.table("ka_app_settings").upsert({"key": key, "value": value}).execute()
