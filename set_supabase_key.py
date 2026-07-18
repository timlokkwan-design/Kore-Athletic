"""Write Supabase service_key into .streamlit/secrets.toml (interactive)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECRETS = ROOT / ".streamlit" / "secrets.toml"
URL = "https://iuyatardbzebxxmmgquy.supabase.co"


def main() -> None:
    print("=== 设定 Supabase service_key ===\n")
    print("请到 Supabase → Project Settings → API")
    print("复制 Secret key（sb_secret_... 开头，约 41 字符）\n")

    key = input("请粘贴 service_key，然后按 Enter：\n> ").strip().strip('"').strip("'")
    if not key:
        print("\n[X] 未输入 key，已取消")
        return

    if key.startswith("sb_publishable"):
        print("\n[X] 这是 publishable key，不能用。请改用 sb_secret_ 或 service_role key")
        return

    if not (key.startswith("sb_secret_") or key.startswith("eyJ")):
        print("\n[!] 警告：key 格式 unusual，但仍会写入。若失败请重新复制。")

    content = f'''# 本机 Supabase 设定（此档不会上传 GitHub）

[coach]
username = "ktll"
password = "170330"

[supabase]
url = "{URL}"
service_key = "{key}"
'''
    SECRETS.parent.mkdir(parents=True, exist_ok=True)
    SECRETS.write_text(content, encoding="utf-8")

    print(f"\n[OK] 已写入 {SECRETS}")
    print(f"[OK] url = {URL}")
    print(f"[OK] key 长度 = {len(key)} 字符")
    print("\n下一步：")
    print("  1. 双击 檢查Supabase.bat 确认连接")
    print("  2. 关掉 start.bat 再重新启动")
    print("  3. 系统设定 → 网站内容 → 底部应显示 Supabase 已启用")


if __name__ == "__main__":
    main()
