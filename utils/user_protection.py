"""Protect student/parent accounts across deploys and concurrent saves.

FOREVER RULE: App updates/redeploys must never wipe real user accounts.
Users are independently snapshotted and every save merges with the live DB.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from utils.config import DATA_DIR, USERS_FILE
from utils.helpers import safe_str

USERS_BACKUP_SETTING_KEY = "users_account_backup"
PROTECTED_ROLES = frozenset({"student", "parent", "pending", "removed", "coach"})
# Demo seeds only — real registrations are never in this set.
DISPOSABLE_USERNAMES = frozenset({"student1", "student2", "student3", "parent1"})


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def users_backup_dir() -> Path:
    path = _project_root() / DATA_DIR / "backups" / "users"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ensure_user_cols(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy() if df is not None else pd.DataFrame(columns=columns)
    for col in columns:
        if col not in out.columns:
            out[col] = None
    if out.empty:
        return pd.DataFrame(columns=columns)
    return out[columns]


def is_protected_account(row: dict | pd.Series) -> bool:
    username = safe_str(row.get("username") if hasattr(row, "get") else row["username"])
    role = safe_str(row.get("role") if hasattr(row, "get") else row["role"])
    if not username:
        return False
    if username in DISPOSABLE_USERNAMES:
        return False
    return role in PROTECTED_ROLES


def protected_usernames(df: pd.DataFrame) -> set[str]:
    if df is None or df.empty:
        return set()
    names: set[str] = set()
    for _, row in df.iterrows():
        if is_protected_account(row):
            names.add(safe_str(row["username"]))
    return names


def count_protected(df: pd.DataFrame) -> dict[str, int]:
    if df is None or df.empty:
        return {"total": 0, "student": 0, "parent": 0, "pending": 0, "coach": 0, "removed": 0}
    counts = {"total": 0, "student": 0, "parent": 0, "pending": 0, "coach": 0, "removed": 0}
    for _, row in df.iterrows():
        if not is_protected_account(row):
            continue
        counts["total"] += 1
        role = safe_str(row["role"])
        if role in counts:
            counts[role] += 1
    return counts


def merge_users_preserving_accounts(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
    columns: list[str],
    *,
    drop_usernames: set[str] | frozenset[str] | None = None,
) -> pd.DataFrame:
    """Upsert incoming rows; keep any protected accounts missing from incoming."""
    drop = {safe_str(u) for u in (drop_usernames or set()) if safe_str(u)}
    existing = _ensure_user_cols(existing, columns)
    incoming = _ensure_user_cols(incoming, columns)

    by_user: dict[str, dict] = {}
    for _, row in existing.iterrows():
        username = safe_str(row["username"])
        if not username or username in drop:
            continue
        by_user[username] = {col: row.get(col) for col in columns}

    for _, row in incoming.iterrows():
        username = safe_str(row["username"])
        if not username or username in drop:
            continue
        by_user[username] = {col: row.get(col) for col in columns}

    if not by_user:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(list(by_user.values()), columns=columns).reset_index(drop=True)


def _df_to_records(df: pd.DataFrame, columns: list[str]) -> list[dict]:
    clean = _ensure_user_cols(df, columns)
    if clean.empty:
        return []
    records = []
    for row in clean.to_dict(orient="records"):
        item = {}
        for col in columns:
            val = row.get(col)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                item[col] = None
            else:
                item[col] = str(val)
        records.append(item)
    return records


def snapshot_users_backup(df: pd.DataFrame, columns: list[str], *, reason: str = "auto") -> dict:
    """Write independent users backup (local file + Supabase app setting when available)."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    records = _df_to_records(df, columns)
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "count": len(records),
        "protected": count_protected(df),
        "columns": list(columns),
        "users": records,
    }

    backup_dir = users_backup_dir()
    stamped = backup_dir / f"users_{stamp}.csv"
    latest = backup_dir / "users_latest.csv"
    csv_text = _ensure_user_cols(df, columns).to_csv(index=False, encoding="utf-8-sig")
    stamped.write_text(csv_text, encoding="utf-8-sig")
    latest.write_text(csv_text, encoding="utf-8-sig")
    (backup_dir / "users_latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Keep last 30 CSV snapshots
    stamped_files = sorted(backup_dir.glob("users_20*.csv"), reverse=True)
    for old in stamped_files[30:]:
        try:
            old.unlink()
        except OSError:
            pass

    try:
        from utils.supabase_config import is_supabase_enabled
        from utils.supabase_io import write_app_setting

        if is_supabase_enabled():
            write_app_setting(USERS_BACKUP_SETTING_KEY, payload)
    except Exception:
        # Backup file on disk is enough if remote setting write fails.
        pass

    return {
        "saved_at": payload["saved_at"],
        "count": payload["count"],
        "protected": payload["protected"],
        "path": str(latest),
        "reason": reason,
    }


def load_users_backup_payload() -> dict | None:
    try:
        from utils.supabase_config import is_supabase_enabled
        from utils.supabase_io import read_app_setting

        if is_supabase_enabled():
            remote = read_app_setting(USERS_BACKUP_SETTING_KEY)
            if isinstance(remote, dict) and remote.get("users") is not None:
                return remote
    except Exception:
        pass

    latest_json = users_backup_dir() / "users_latest.json"
    if latest_json.exists():
        try:
            return json.loads(latest_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return None


def backup_payload_to_df(payload: dict, columns: list[str]) -> pd.DataFrame:
    users = payload.get("users") or []
    if not users:
        return pd.DataFrame(columns=columns)
    return _ensure_user_cols(pd.DataFrame(users), columns)


def read_users_csv_bytes(df: pd.DataFrame, columns: list[str]) -> bytes:
    return _ensure_user_cols(df, columns).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def build_users_only_backup() -> tuple[bytes, str]:
    from utils.data_store import USER_COLUMNS, load_users

    df = load_users()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    return read_users_csv_bytes(df, USER_COLUMNS), f"kore-users-only_{stamp}.csv"


def read_live_users(columns: list[str]) -> pd.DataFrame:
    """Always hit storage (bypass session cache) before protective merges."""
    from utils.session_cache import drop_cache_keys
    from utils.supabase_config import is_supabase_enabled

    drop_cache_keys(USERS_FILE, "coach_pending_summary")
    if is_supabase_enabled():
        from utils.supabase_io import read_csv_table

        return read_csv_table(USERS_FILE, columns)

    path = _project_root() / DATA_DIR / USERS_FILE
    if not path.exists():
        return pd.DataFrame(columns=columns)
    return _ensure_user_cols(pd.read_csv(path), columns)


class UserAccountGuardError(RuntimeError):
    """Raised when a save would wipe protected accounts."""


def protected_save_users(
    incoming: pd.DataFrame,
    columns: list[str],
    *,
    allow_account_loss: bool = False,
    drop_usernames: set[str] | frozenset[str] | None = None,
    reason: str = "save",
) -> pd.DataFrame:
    """Merge-safe users write. Never drops protected accounts unless explicitly allowed."""
    from utils.supabase_config import is_supabase_enabled
    from utils.supabase_io import write_csv_table_replace

    live = read_live_users(columns)
    snapshot_users_backup(live, columns, reason=f"pre-{reason}")

    if allow_account_loss:
        merged = _ensure_user_cols(incoming, columns)
        if drop_usernames:
            drop = {safe_str(u) for u in drop_usernames}
            if not merged.empty:
                merged = merged[~merged["username"].astype(str).isin(drop)].reset_index(drop=True)
    else:
        merged = merge_users_preserving_accounts(
            live,
            incoming,
            columns,
            drop_usernames=drop_usernames,
        )
        live_protected = protected_usernames(live)
        merged_protected = protected_usernames(merged)
        lost = live_protected - merged_protected
        if lost:
            # Hard stop — re-merge from live so a bug cannot delete students.
            merged = merge_users_preserving_accounts(live, incoming, columns, drop_usernames=drop_usernames)
            still_lost = live_protected - protected_usernames(merged)
            if still_lost:
                raise UserAccountGuardError(
                    "拒絕覆寫 users：會令受保護帳號消失：" + "、".join(sorted(still_lost)[:20])
                )

    # Prefer upsert when Supabase unique(username) exists; always merge-replace as safe path.
    if is_supabase_enabled():
        try:
            from utils.supabase_io import upsert_users_table

            upsert_users_table(merged, columns)
        except Exception:
            write_csv_table_replace(USERS_FILE, merged, columns)
    else:
        write_csv_table_replace(USERS_FILE, merged, columns)

    from utils.session_cache import invalidate_data_cache

    invalidate_data_cache()
    snapshot_users_backup(merged, columns, reason=f"post-{reason}")
    return merged


def restore_users_from_backup(
    *,
    payload: dict | None = None,
    uploaded_df: pd.DataFrame | None = None,
) -> dict:
    """Restore accounts by merging backup into live users (never deletes extras)."""
    from utils.data_store import USER_COLUMNS

    columns = USER_COLUMNS
    if uploaded_df is not None:
        incoming = _ensure_user_cols(uploaded_df, columns)
    else:
        payload = payload or load_users_backup_payload()
        if not payload:
            raise FileNotFoundError("找不到用戶帳號備份")
        incoming = backup_payload_to_df(payload, columns)

    if incoming.empty:
        raise ValueError("備份沒有任何用戶資料")

    merged = protected_save_users(incoming, columns, allow_account_loss=False, reason="restore")
    return {
        "restored_rows": len(incoming),
        "total_after": len(merged),
        "protected_after": count_protected(merged),
    }
