"""One-shot migration — hash all plaintext passwords in users.csv."""
from __future__ import annotations

import sys

from utils.data_store import load_users, save_users
from utils.passwords import hash_password, is_hashed
from utils.helpers import safe_str


def migrate_passwords() -> tuple[int, int]:
    users = load_users()
    if users.empty:
        return 0, 0
    users["password"] = users["password"].astype(str)
    migrated = 0
    skipped = 0
    for idx, row in users.iterrows():
        stored = safe_str(row.get("password"))
        if not stored or stored in {"nan", "None"}:
            skipped += 1
            continue
        if is_hashed(stored):
            skipped += 1
            continue
        if len(stored) < 3:
            skipped += 1
            continue
        users.loc[idx, "password"] = hash_password(stored)
        migrated += 1
    if migrated:
        save_users(users)
    return migrated, skipped


def main() -> int:
    migrated, skipped = migrate_passwords()
    print(f"已加密 {migrated} 個帳號密碼，{skipped} 個略過（已是加密或空白）。")
    if migrated:
        print("注意：加密後舊明文密碼無法還原，請確認已備份 users.csv。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
