"""Check whether Supabase secrets are configured (run: python check_supabase.py)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECRETS = ROOT / ".streamlit" / "secrets.toml"


def main() -> None:
    print("=== Supabase 设定检查 ===\n")

    if not SECRETS.exists():
        print(f"[X] 找不到 {SECRETS}")
        print("    请复制 secrets.toml.example 为 secrets.toml")
        return

    print(f"[OK] 找到 secrets.toml")

    text = SECRETS.read_text(encoding="utf-8")
    has_url = "iuyatardbzebxxmmgquy.supabase.co" in text or "supabase.co" in text
    has_key_line = "service_key" in text

    if has_url:
        print("[OK] 有 supabase url")
    else:
        print("[X] 缺少 supabase url")

    if 'service_key = ""' in text or "service_key = ''" in text:
        print("[X] service_key 还是空的 — 请贴上 service_role key")
        return

    if not has_key_line:
        print("[X] 缺少 service_key 行")
        return

    print("[OK] service_key 已填写")

    try:
        from utils.supabase_config import get_supabase_credentials, is_supabase_enabled

        url, key = get_supabase_credentials()
        if not is_supabase_enabled():
            print("[X] App 读不到 url 或 service_key（检查格式）")
            return

        print(f"[OK] url = {url}")
        print(f"[OK] key 长度 = {len(key or '')} 字符")

        from supabase import create_client

        client = create_client(url, key)
        resp = client.table("ka_app_settings").select("key").limit(1).execute()
        print(f"[OK] 已连上 Supabase（ka_app_settings 可读）")
        print("\n=== 成功！请重启 start.bat，再到 系统设定 → 网站内容 看底部 ===")
    except Exception as exc:
        print(f"[X] 连接失败: {exc}")
        print("    常见原因：key 不完整、用了 anon key、或未执行 schema.sql")


if __name__ == "__main__":
    main()
