"""Reset all training/score data for production launch — keeps coach account only."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from utils.config import (
    ATTENDANCE_FILE,
    AVATARS_DIR,
    COMPETITIONS_FILE,
    COMP_ENTRIES_FILE,
    DATA_DIR,
    DEFAULT_PERIODIZATION,
    INJURIES_FILE,
    LOGS_FILE,
    PENDING_FILE,
    PENDING_SPECIALTY_FILE,
    PERIOD_FILE,
    PROGRAMS_FILE,
    RACE_RECORDS_FILE,
    TEMPLATES_FILE,
    USERS_FILE,
    VIDEOS_FILE,
    WELLNESS_FILE,
)
from utils.data_store import (
    ATTENDANCE_COLUMNS,
    COMP_COLUMNS,
    COMP_ENTRY_COLUMNS,
    INJURY_COLUMNS,
    LOG_COLUMNS,
    PENDING_COLUMNS,
    PENDING_SPECIALTY_COLUMNS,
    PROGRAM_COLUMNS,
    RACE_COLUMNS,
    TEMPLATE_COLUMNS,
    USER_COLUMNS,
    VIDEO_COLUMNS,
    WELLNESS_COLUMNS,
    save_periodization,
    save_users,
)
from utils.passwords import hash_password, is_hashed
from utils.production import enable_production_mode
from utils.site_content import DEFAULT_SITE_CONTENT, load_site_content

ROOT = Path(__file__).resolve().parent
DATA = ROOT / DATA_DIR
BACKUPS = DATA / "backups"
AVATARS = DATA / AVATARS_DIR

EMPTY_CSVS: dict[str, list[str]] = {
    PROGRAMS_FILE: PROGRAM_COLUMNS,
    LOGS_FILE: LOG_COLUMNS,
    WELLNESS_FILE: WELLNESS_COLUMNS,
    ATTENDANCE_FILE: ATTENDANCE_COLUMNS,
    INJURIES_FILE: INJURY_COLUMNS,
    COMPETITIONS_FILE: COMP_COLUMNS,
    COMP_ENTRIES_FILE: COMP_ENTRY_COLUMNS,
    VIDEOS_FILE: VIDEO_COLUMNS,
    TEMPLATES_FILE: TEMPLATE_COLUMNS,
    PENDING_FILE: PENDING_COLUMNS,
    PENDING_SPECIALTY_FILE: PENDING_SPECIALTY_COLUMNS,
    RACE_RECORDS_FILE: RACE_COLUMNS,
    "training_menus.csv": PROGRAM_COLUMNS,
}

DEFAULT_COACH = "ktll"


def _empty_df(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _write_empty_csv(path: Path, columns: list[str]) -> None:
    _empty_df(columns).to_csv(path, index=False, encoding="utf-8-sig")


def _backup_data() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = BACKUPS / stamp
    dest.mkdir(parents=True, exist_ok=True)
    for item in DATA.iterdir():
        if item.name in {"backups", ".production"}:
            continue
        target = dest / item.name
        if item.is_dir():
            if item.exists():
                shutil.copytree(item, target)
        elif item.is_file():
            shutil.copy2(item, target)
    return dest


def _coach_row_from(users: pd.DataFrame) -> dict:
    if not users.empty:
        coaches = users[users["role"].astype(str) == "coach"]
        if not coaches.empty:
            row = coaches.iloc[0].to_dict()
            return {col: row.get(col, "") for col in USER_COLUMNS}
    row = {col: "" for col in USER_COLUMNS}
    row.update({
        "username": DEFAULT_COACH,
        "name": "關添樂",
        "role": "coach",
        "password": "170330",
    })
    return row


def _clear_avatars() -> int:
    if not AVATARS.exists():
        AVATARS.mkdir(parents=True, exist_ok=True)
        return 0
    count = 0
    for f in AVATARS.iterdir():
        if f.is_file():
            f.unlink()
            count += 1
    return count


def _reset_site_content() -> None:
    from utils.site_content import _content_path

    current = load_site_content()
    cleaned = {key: current.get(key, DEFAULT_SITE_CONTENT[key]) for key in DEFAULT_SITE_CONTENT}
    cleaned["public_pb_leaderboard"] = False
    for key in ("club_intro", "coach_intro", "contact_info", "join_process"):
        cleaned[key] = str(cleaned.get(key) or "")
    _content_path().write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _default_periodization() -> dict:
    year = date.today().year
    target = f"{year + 1}-04-15"
    return {
        "global_phase": DEFAULT_PERIODIZATION["global_phase"],
        "global_week_theme": DEFAULT_PERIODIZATION["global_week_theme"],
        "comp_target_date": target,
    }


def reset_for_production(*, keep_coach_password: bool = True) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    backup_path = _backup_data()

    users = pd.DataFrame(columns=USER_COLUMNS)
    users_path = DATA / USERS_FILE
    if users_path.exists():
        users = pd.read_csv(users_path)
        for col in USER_COLUMNS:
            if col not in users.columns:
                users[col] = ""
        users = users[USER_COLUMNS]

    coach = _coach_row_from(users)
    if not keep_coach_password:
        coach["password"] = "170330"
    stored = str(coach.get("password", ""))
    if not is_hashed(stored):
        coach["password"] = hash_password(stored)
    save_users(pd.DataFrame([coach]))

    for filename, columns in EMPTY_CSVS.items():
        _write_empty_csv(DATA / filename, columns)

    save_periodization(_default_periodization())

    avatar_count = _clear_avatars()
    _reset_site_content()
    enable_production_mode()

    return {
        "backup": str(backup_path),
        "coach_username": coach.get("username", DEFAULT_COACH),
        "avatars_removed": avatar_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset KORE ATHLETIC data for production launch")
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset coach password to default 170330",
    )
    args = parser.parse_args()

    print("=== KORE ATHLETIC 正式上線重置 ===")
    print("將會：")
    print("  · 備份整個 data/ 資料夾")
    print("  · 清除所有訓練、成績、出席、比賽等紀錄")
    print("  · 只保留教練帳號")
    print("  · 清除學員頭像")
    print("  · 關閉 PB 公開顯示")
    print("  · 啟用正式模式（不再自動建立測試資料）")
    print()

    if not args.yes:
        try:
            answer = input("確定繼續？輸入 YES 才會執行：").strip()
        except EOFError:
            answer = ""
        if answer != "YES":
            print("已取消。")
            return 1

    result = reset_for_production(keep_coach_password=not args.reset_password)
    print()
    print("=== 重置完成 ===")
    print(f"  備份位置：{result['backup']}")
    print(f"  教練帳號：{result['coach_username']}")
    print(f"  已刪除頭像：{result['avatars_removed']} 個")
    print()
    print("下一步：")
    print("  1. 雙擊 start.bat 啟動系統")
    print("  2. 用教練帳號登入，立即修改密碼")
    print("  3. 在教練平台建立新賽季課表及週期設定")
    print("  4. 在「系統設定 → 網站內容」確認訪客專區文案")
    return 0


if __name__ == "__main__":
    sys.exit(main())
