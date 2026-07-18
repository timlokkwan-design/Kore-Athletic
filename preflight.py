"""啟動前檢查 — 確認所有模組可正常載入."""

import sys


def main() -> int:
    checks = [
        ("utils.config", "APP_NAME"),
        ("utils.grades", "U18_GRADES"),
        ("utils.helpers", "get_grade"),
        ("utils.data_store", "get_pb_by_event"),
        ("utils.data_store", "get_user"),
        ("utils.data_store", "init_sample_data"),
    ]
    print("=== KORE ATHLETIC 啟動檢查 ===")
    for module, name in checks:
        try:
            mod = __import__(module, fromlist=[name])
            getattr(mod, name)
            print(f"  [OK] {module}.{name}")
        except Exception as e:
            print(f"  [FAIL] {module}.{name} -> {e}")
            return 1
    try:
        import app  # noqa: F401
        from views.register_view import render_register_view  # noqa: F401
        print("  [OK] app + register_view")
    except Exception as e:
        print(f"  [FAIL] app -> {e}")
        return 1
    print("=== 全部通過，可以啟動 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
