"""Emergency coach password reset — run locally when coach cannot log in."""

from __future__ import annotations

import sys

from utils.data_store import load_users, set_user_password

DEFAULT_COACH = "ktll"
DEFAULT_PASSWORD = "170330"


def reset_coach_password(username: str = DEFAULT_COACH, new_password: str = DEFAULT_PASSWORD) -> tuple[bool, str]:
    users = load_users()
    if users.empty:
        return False, "找不到 users.csv 資料"
    mask = users["username"].astype(str).eq(username) & users["role"].astype(str).eq("coach")
    if not mask.any():
        return False, f"找不到教練帳號：{username}"
    return set_user_password(username, new_password.strip())


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COACH
    password = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PASSWORD
    ok, msg = reset_coach_password(username, password)
    print(msg)
    if ok:
        print(f"請使用帳號 {username} 及新密碼登入 http://localhost:8502")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
