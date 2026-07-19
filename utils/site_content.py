"""Public site copy — editable by coach, shown in visitor zone."""
from __future__ import annotations

import json
from pathlib import Path

from utils.config import APP_NAME, COACH_NAME
from utils.helpers import safe_str

SITE_CONTENT_FILE = "site_content.json"
SITE_CONTENT_KEY = "site_content"

DEFAULT_SITE_CONTENT: dict = {
    "club_intro": (
        f"{APP_NAME} 由{COACH_NAME}教練帶領，專注青少年田徑訓練，"
        "涵蓋短跑、中長跑、跨欄及田賽。我們以科學化週期訓練及比賽準備，"
        "協助學員突破個人最佳成績。"
    ),
    "coach_intro": (
        f"{COACH_NAME}教練具多年田徑帶隊及青訓經驗，"
        "重視技術基礎、訓練紀律與比賽心理，"
        "並按學員專項及程度制訂個人化計劃。"
    ),
    "contact_info": (
        "查詢及報名：請透過 Instagram 私信本會，或提交「註冊新學員」申請。"
        "教練會在系統內審批，不公開電話號碼。"
    ),
    "instagram_handle": "koreathletic_kwansir",
    "coach_whatsapp": "",
    "join_process": (
        "1. 點選選單（☰）→「註冊新學員」填寫資料\n"
        "2. 等待教練審批\n"
        "3. 核准後使用帳號登入學生平台"
    ),
    "public_pb_leaderboard": False,
}


def _content_path() -> Path:
    base = Path(__file__).resolve().parent.parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base / SITE_CONTENT_FILE


def _merge_site_content(data: dict) -> dict:
    merged = {**DEFAULT_SITE_CONTENT, **data}
    merged["public_pb_leaderboard"] = bool(merged.get("public_pb_leaderboard"))
    return merged


def load_site_content() -> dict:
    from utils.supabase_config import is_supabase_enabled

    if is_supabase_enabled():
        from utils.supabase_io import read_app_setting

        stored = read_app_setting(SITE_CONTENT_KEY)
        if stored:
            return _merge_site_content(stored)
        merged = dict(DEFAULT_SITE_CONTENT)
        from utils.supabase_io import write_app_setting

        write_app_setting(SITE_CONTENT_KEY, merged)
        return merged

    path = _content_path()
    if not path.exists():
        merged = dict(DEFAULT_SITE_CONTENT)
        path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return merged
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}
    return _merge_site_content(data)


def save_site_content(data: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in

    enforce_coach_if_logged_in()
    current = load_site_content()
    for key in DEFAULT_SITE_CONTENT:
        if key in data:
            current[key] = data[key]
    current["public_pb_leaderboard"] = bool(
        data.get("public_pb_leaderboard", current["public_pb_leaderboard"])
    )
    for key in (
        "club_intro", "coach_intro", "contact_info", "join_process",
        "coach_whatsapp", "instagram_handle",
    ):
        current[key] = safe_str(current.get(key))

    from utils.supabase_config import is_supabase_enabled

    if is_supabase_enabled():
        from utils.supabase_io import write_app_setting

        write_app_setting(SITE_CONTENT_KEY, current)
        return

    _content_path().write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_pb_public() -> bool:
    return bool(load_site_content().get("public_pb_leaderboard"))
