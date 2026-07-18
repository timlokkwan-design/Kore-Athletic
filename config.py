"""Training menu and app configuration."""

from datetime import date

# Default daily training menu (can be overridden via CSV)
DEFAULT_MENU = {
    "date": date.today().isoformat(),
    "event": "400m",
    "reps": 6,
    "target_seconds": 65.0,
    "description": "400m x 6，組間休息 90 秒",
    "notes": "前兩趟輕鬆跑，後四趟配速跑",
}

# Common injury / discomfort areas for the form
INJURY_OPTIONS = [
    "無不適",
    "左膝",
    "右膝",
    "左踝",
    "右踝",
    "左大腿後側",
    "右大腿後側",
    "左小腿",
    "右小腿",
    "髖部",
    "下背",
    "其他",
]

DATA_DIR = "data"
MENUS_FILE = "training_menus.csv"
LOGS_FILE = "training_logs.csv"
