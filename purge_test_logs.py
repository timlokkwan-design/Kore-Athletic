"""Remove demo student training logs (陳大文、林明美等) from Supabase/CSV."""
from __future__ import annotations

import sys

from utils.data_store import purge_test_student_records
from utils.supabase_config import is_supabase_enabled


def main() -> int:
    print("=== 清除測試學員日誌 ===")
    print("  · 陳大文、林明美、張豪傑、陳家長 的訓練紀錄")
    print("  · 不刪除真實學員、不清除課表")
    if not is_supabase_enabled():
        print("\n[!] 未偵測到 Supabase，將清除本機 CSV")
    confirm = input("\n確定執行？(y/N): ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("已取消")
        return 0
    stats = purge_test_student_records(clear_programs=False)
    print(f"  日誌刪除：{stats.get('logs_removed', 0)} 筆")
    print("=== 完成 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
