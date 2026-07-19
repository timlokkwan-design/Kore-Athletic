"""KORE ATHLETIC — full V6 configuration."""

from datetime import date

from utils.grades import U18_GRADES, WIND_EVENTS

APP_NAME = "KORE ATHLETIC"
APP_SUBTITLE = "關添樂教練田徑訓練與成績管理系統"
APP_VERSION = "2026.07.19-112"
COACH_NAME = "關添樂"
EMAIL_DOMAIN = "@kore-athletic.app"

TRAIN_TYPES = {
    "間歇跑": {"weight": 1.5, "category": "speed"},
    "節奏跑": {"weight": 1.2, "category": "endurance"},
    "恢復跑": {"weight": 0.5, "category": "endurance"},
    "技術課": {"weight": 0.6, "category": "technique"},
    "肌力課": {"weight": 0.8, "category": "strength"},
    "比賽": {"weight": 0.7, "category": "field"},
    "休息": {"weight": 0.0, "category": "rest"},
    "訓練": {"weight": 1.2, "category": "speed"},
    "待排課": {"weight": 0.0, "category": "pending"},
}

TRAIN_TYPE_OPTIONS = list(TRAIN_TYPES.keys())


def normalize_train_type(train_type: str) -> str:
    """Map legacy labels (e.g. 田賽) to current TRAIN_TYPES keys."""
    t = str(train_type or "").strip()
    if t == "田賽":
        return "比賽"
    return t if t in TRAIN_TYPES else "間歇跑"


TYPE_CATEGORY_COLORS = {
    "speed": "#fee2e2", "endurance": "#dbeafe", "technique": "#f3e8ff",
    "strength": "#ffedd5", "field": "#dcfce7", "rest": "#f1f5f9",
    "pending": "#fef3c7",
}

# Month calendar cell backgrounds — synced with views/components/calendar_theme.py
CALENDAR_BG_TRAINING = "#B8D4F8"
CALENDAR_BG_COMPETITION = "#FFCACA"
CALENDAR_BG_REST = "#D5DCE5"
CALENDAR_BG_EMPTY = "#E8EDF3"

GROUP_OPTIONS = ["短跑組", "中長跑組", "跨欄組", "全體組員"]

# 訓練時間表：儲存時間地點時，同步至所有組別（全隊同一時間地點）
SCHEDULE_UNIFIED_GROUPS = ["短跑組", "中長跑組", "跨欄組", "全體組員"]
# 向後相容
SCHEDULE_LINKED_GROUPS = SCHEDULE_UNIFIED_GROUPS

GROUP_DISPLAY = {
    "短跑組": "短跑",
    "中長跑組": "中長跑",
    "跨欄組": "跨欄",
    "全體組員": "全部學員",
}

CALENDAR_GROUP_FILTERS = [
    ("全部組別", None),
    ("短跑", "短跑組"),
    ("中長跑", "中長跑組"),
    ("跨欄", "跨欄組"),
    ("全部學員", "全體組員"),
]

LEGACY_GROUP_MAP = {
    "短跑組 (100-400m)": "短跑組",
    "中長跑組 (800-5000m)": "中長跑組",
    "跨欄及田賽組": "跨欄組",
    "全體組員": "全體組員",
}


def normalize_group(group: str) -> str:
    g = str(group or "").strip()
    if g in GROUP_OPTIONS:
        return g
    return LEGACY_GROUP_MAP.get(g, g or "短跑組")


def group_display_label(group: str) -> str:
    """User-facing group name (短跑 / 中長跑 / 跨欄 / 全部學員)."""
    return GROUP_DISPLAY.get(normalize_group(group), normalize_group(group))


WEEKDAY_OPTIONS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
WEEKDAY_SHORT = ["一", "二", "三", "四", "五", "六", "日"]
VENUE_OPTIONS = ["斧山道運動場", "將軍澳運動場", "葵涌運動場", "其他"]
DEFAULT_VENUE = "斧山道運動場"
SPECIALTY_TO_GROUP = {
    "短跑": "短跑組",
    "中長跑": "中長跑組",
    "跨欄": "跨欄組",
    "田項": "跨欄組",
    "田賽": "跨欄組",  # legacy
}
PHASE_OPTIONS = ["準備期", "強化期", "調整期", "賽季期", "恢復期"]
WEEK_THEME_OPTIONS = ["速度週", "速度耐力週", "技術週", "減量週", "恢復週"]
SPECIALTY_OPTIONS = ["短跑", "中長跑", "跨欄", "田項"]
GENDER_OPTIONS = ["男", "女"]
HK_PERMANENT_OPTIONS = ["是", "否"]
LEAVE_REASONS = ["病假", "學校活動", "家庭原因", "受傷", "其他"]

EVENTS = [
    "100米", "200米", "400米", "800米", "1500米", "3000米", "5000米",
    "110米欄", "100米欄", "400米欄", "跳遠", "三級跳", "跳高", "撐竿跳",
    "鉛球", "鐵餅", "標槍", "鏈球",
]
FIELD_EVENTS = ["跳遠", "三級跳", "跳高", "撐竿跳", "鉛球", "鐵餅", "標槍", "鏈球"]

TECHNIQUE_LIB = [
    {"issue": "起跑反應慢", "fix": "加強聽令練習、爆發式深蹲跳"},
    {"issue": "途中步頻低", "fix": "小欄架步頻訓練、節拍器輔助"},
    {"issue": "跨欄節奏不穩", "fix": "縮短間距欄架練習、節奏標記"},
    {"issue": "跳遠起跳角度過大", "fix": "標記起跳點、助跑節奏固定"},
    {"issue": "投擲出手角度偏低", "fix": "牆面出手角度練習、核心穩定訓練"},
    {"issue": "彎道傾斜不足", "fix": "彎道跑姿專項、離心力適應"},
]

TAPER_DAYS = {"100米": 3, "200米": 4, "400米": 5, "800米": 7, "1500米": 10, "5000米": 14}

DEFAULT_PERIODIZATION = {
    "global_phase": "準備期",
    "global_week_theme": "速度週",
    "comp_target_date": "2026-04-15",
}

INJURY_OPTIONS = [
    "無不適", "左膝", "右膝", "左踝", "右踝", "左大腿後側", "右大腿後側",
    "左小腿", "右小腿", "髖部", "下背", "其他",
]

DATA_DIR = "data"
AVATARS_DIR = "avatars"
PROGRAMS_FILE = "programs.csv"
LOGS_FILE = "training_logs.csv"
USERS_FILE = "users.csv"
WELLNESS_FILE = "wellness.csv"
PERIOD_FILE = "periodization.csv"
ATTENDANCE_FILE = "attendance.csv"
INJURIES_FILE = "injuries.csv"
COMPETITIONS_FILE = "competitions.csv"
COMP_ENTRIES_FILE = "comp_entries.csv"
VIDEOS_FILE = "videos.csv"
TEMPLATES_FILE = "templates.csv"
PENDING_FILE = "pending_records.csv"
PENDING_SPECIALTY_FILE = "pending_specialty.csv"
RACE_RECORDS_FILE = "race_records.csv"

MENUS_FILE = PROGRAMS_FILE


def default_program(for_date: str | None = None) -> dict:
    d = for_date or date.today().isoformat()
    return {
        "date": d, "type": "間歇跑", "title": "",
        "group": "短跑組", "sets": 0, "reps": 0, "dist": 0,
        "rest": "", "duration": 0, "rpe": 7,
        "tips": "", "phase": "", "week_theme": "",
        "target_seconds": 65.0, "load": 630,
        "exercises": "", "tech_focus": "", "field_event": "跳遠", "attempts": 10,
        "start_time": "", "end_time": "", "venue": "", "venue_other": "",
    }


def schedule_placeholder_program(for_date: str, *, group: str = "短跑組") -> dict:
    """Empty program row for pre-setting time/venue before workout is written."""
    g = normalize_group(group)
    d = for_date or date.today().isoformat()
    return {
        "date": d,
        "type": "待排課",
        "title": group_display_label(g),
        "group": g,
        "sets": 0,
        "reps": 0,
        "dist": 0,
        "rest": "",
        "duration": 0,
        "rpe": 7,
        "tips": "",
        "phase": "",
        "week_theme": "",
        "target_seconds": 0,
        "load": 0,
        "exercises": "",
        "tech_focus": "",
        "field_event": "",
        "attempts": 0,
        "start_time": "",
        "end_time": "",
        "venue": "",
        "venue_other": "",
    }


DEFAULT_MENU = default_program()

# V6 註冊 — 健康聲明及免責條款原文
HEALTH_DECLARATION_PLACEHOLDER = (
    "如患有哮喘、敏感、長期病患或需要特別照顧，請在此列明；如無，請填「無」"
)
HKAAA_ID_PLACEHOLDER = "如無請填 000"
DEFAULT_HKAAA_ID = "000"

REGISTRATION_DISCLAIMER_ITEMS = [
    ("身體健康：", "確認報名學生身體狀況良好，無任何隱疾、心臟病、哮喘或不適宜進行劇烈田徑訓練之疾病。"),
    ("自負風險：", "明白田徑訓練涉及一定運動風險，本人自願讓子女參與並承擔相關風險。"),
    ("機構免責：", "對於學員因參與是次活動期間因意外、疏忽或不可抗力事件引致的任何個人傷亡或財物損失，主辦機構（KORE ATHLETIC）及教練團隊毋須承擔任何法律及經濟責任。"),
    ("緊急醫療：", "如遇緊急意外，授權主辦機構在無法即時聯絡家長的情況下，採取必要急救措施並安排送院，由此產生的醫療費用由家長自行承擔。"),
    ("遵守指引：", "學員必須嚴格遵守導師及運動場守則，如因不遵從指引引致意外，家長須承擔全部責任。"),
]

REGISTRATION_DISCLAIMER_HTML = ""  # legacy, use REGISTRATION_DISCLAIMER_ITEMS

REGISTRATION_AGREEMENT_LABEL = (
    "家長/監護人同意聲明：本人已仔細閱讀、完全明白並同意上述所有之內容。"
)
