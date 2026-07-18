"""Read/write pandas tables via Supabase PostgreSQL."""
from __future__ import annotations

import pandas as pd

from utils.supabase_config import get_supabase_client

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
}

INTERNAL_COLUMNS = {"row_id"}
INSERT_BATCH = 200


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
    resp = client.table(table).select("*").execute()
    rows = resp.data or []
    if not rows:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(rows)
    drop = [c for c in INTERNAL_COLUMNS if c in df.columns and c not in columns]
    if drop:
        df = df.drop(columns=drop)
    return _ensure_cols(df, columns)


def write_csv_table(filename: str, df: pd.DataFrame, columns: list[str]) -> None:
    table = _table_for_file(filename)
    client = get_supabase_client()
    client.rpc("ka_clear_table", {"tname": table}).execute()
    records = _sanitize_records(_df_to_records(df, columns))
    if not records:
        return
    for i in range(0, len(records), INSERT_BATCH):
        client.table(table).insert(records[i : i + INSERT_BATCH]).execute()


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
