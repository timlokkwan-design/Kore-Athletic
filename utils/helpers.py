"""V6 helper functions."""

from __future__ import annotations

from datetime import date

import pandas as pd

from utils.grades import U18_GRADES, WIND_EVENTS


def to_scalar(v):
    """Convert pandas Series/DataFrame cells to a plain Python value."""
    if isinstance(v, pd.Series):
        return None if v.empty else v.iloc[0]
    if isinstance(v, pd.DataFrame):
        return None if v.empty else v.iloc[0, 0]
    return v


def is_missing(v) -> bool:
    v = to_scalar(v)
    if v is None:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def safe_int(v, default: int = 0) -> int:
    v = to_scalar(v)
    if is_missing(v):
        return default
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def safe_float(v, default: float = 0.0) -> float:
    v = to_scalar(v)
    if is_missing(v):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def safe_str(v, default: str = "") -> str:
    v = to_scalar(v)
    if is_missing(v):
        return default
    s = str(v).strip()
    return default if s.lower() == "nan" else s


def normalize_date_str(d) -> str:
    """Normalize CSV / date values to YYYY-MM-DD."""
    s = safe_str(d)
    return s[:10] if len(s) >= 10 else s


def format_birth_display(user: dict | None = None, *, birth_date=None, birth_year=None) -> str:
    if user is not None:
        birth_date = user.get("birth_date")
        birth_year = user.get("birth_year")
    bd = normalize_date_str(birth_date)
    if len(bd) == 10:
        return bd
    y = safe_int(birth_year, 0)
    if y >= 1950:
        return str(y)
    return "—"


def default_birth_date(user: dict | None = None) -> date:
    if user:
        bd = normalize_date_str(user.get("birth_date"))
        if len(bd) == 10:
            try:
                return date.fromisoformat(bd)
            except ValueError:
                pass
        y = safe_int(user.get("birth_year"), 0)
        if y >= 1950:
            return date(y, 1, 1)
    return date(2010, 1, 1)


def birth_fields_from_date(birth: date) -> dict:
    return {"birth_date": birth.isoformat(), "birth_year": birth.year}


def normalize_hkaaa_id(value) -> str:
    s = safe_str(value)
    return s if s else "000"


def parse_time(s) -> float:
    if not s:
        return 9999.0
    s = str(s).strip()
    if ":" in s:
        parts = s.split(":")
        return float(parts[0]) * 60 + float(parts[1])
    return float(s) if s else 9999.0


def parse_field_score(s) -> float:
    text = safe_str(s).lower().replace("m", "").replace("cm", "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def get_grade(item: str, score: str, wind: float = 0) -> str:
    grades = U18_GRADES.get(item)
    if not grades:
        return "-"
    t = parse_time(score)
    if item in WIND_EVENTS and wind > 2.0:
        return "風速無效"
    if t <= grades["A"]:
        return "A"
    if t <= grades["B"]:
        return "B"
    if t <= grades["C"]:
        return "C"
    return "D"


def is_wind_valid(item: str, wind: float) -> bool:
    return not (item in WIND_EVENTS and wind > 2.0)


def needs_wind(item: str) -> bool:
    """Whether an event requires wind speed (m/s) input."""
    return item in WIND_EVENTS


def infer_train_type(text: str, fallback: str = "間歇跑") -> str:
    """Guess calendar category from free-text workout plan."""
    from utils.config import TRAIN_TYPE_OPTIONS, normalize_train_type

    fb = normalize_train_type(fallback)
    blob = safe_str(text)
    if not blob:
        return fb
    if "肌力" in blob or "深蹲" in blob or "重量" in blob:
        return "肌力課"
    if "技術" in blob or "欄架" in blob or "起跑" in blob:
        return "技術課"
    if "節奏" in blob:
        return "節奏跑"
    if "恢復" in blob or "慢跑" in blob:
        return "恢復跑"
    return fb if fb in TRAIN_TYPE_OPTIONS else "間歇跑"


def workout_detail(prog: dict) -> str:
    """Free-text run/workout plan (supports mixed distances). Stored in `rest`."""
    rest = safe_str(prog.get("rest"))
    sets, reps, dist = safe_int(prog.get("sets")), safe_int(prog.get("reps")), safe_int(prog.get("dist"))
    target = safe_float(prog.get("target_seconds"))
    if sets and reps and dist and not rest:
        lines = [f"{sets}組 × {reps}趟 × {dist}m"]
        if target > 0:
            lines.append(f"目標 {target:g} 秒")
        return "\n".join(lines)
    if rest:
        return rest
    exercises = safe_str(prog.get("exercises"))
    if exercises:
        return exercises
    return safe_str(prog.get("tech_focus"))


def program_specs(p: dict) -> str:
    tp = safe_str(p.get("type"))
    if tp in ("比賽", "休息"):
        return ""
    detail = workout_detail(p)
    if detail:
        first = detail.split("\n")[0].strip()
        return first[:48] + ("…" if len(first) > 48 else "")
    tips = safe_str(p.get("tips"))
    if tips:
        return tips[:48]
    return safe_str(p.get("title"), "-")


def resolve_venue(prog: dict) -> str:
    venue = safe_str(prog.get("venue"))
    if venue == "其他":
        return safe_str(prog.get("venue_other")) or "（待通知）"
    return venue or "（待設定）"


def format_train_duration(minutes: int) -> str:
    """Format minutes as e.g. 1小時30分 / 45分鐘."""
    m = max(0, int(minutes or 0))
    if m == 0:
        return "0分鐘"
    h, r = divmod(m, 60)
    if h and r:
        return f"{h}小時{r}分"
    if h:
        return f"{h}小時"
    return f"{r}分鐘"


def format_timetable_date(date_str: str) -> str:
    from datetime import date as date_cls

    from utils.config import WEEKDAY_SHORT

    try:
        d = date_cls.fromisoformat(normalize_date_str(date_str))
    except ValueError:
        return date_str
    return f"{d.month}月{d.day}日（{WEEKDAY_SHORT[d.weekday()]}）"


def short_group_label(group: str) -> str:
    g = safe_str(group)
    if g.startswith("短跑"):
        return "短跑"
    if g.startswith("中長"):
        return "中長"
    if "跨欄" in g:
        return "跨欄"
    if "田" in g:
        return "田項"
    if g == "全體組員":
        return "全體"
    return g[:4] or "—"


def merge_programs_calendar_summary(progs: list[dict]) -> tuple[str, str]:
    """Combined title + detail when multiple groups share one calendar day."""
    from utils.config import normalize_train_type

    if not progs:
        return "", ""
    if len(progs) == 1:
        return program_calendar_summary(progs[0])
    types = [normalize_train_type(safe_str(p.get("type"))) for p in progs]
    non_rest = [t for t in types if t != "休息"]
    if not non_rest:
        return "休息", ""
    labels = [
        f"{short_group_label(p.get('group'))}:{normalize_train_type(safe_str(p.get('type')))[:2]}"
        for p in progs
        if normalize_train_type(safe_str(p.get("type"))) != "休息"
    ]
    if len(set(non_rest)) == 1:
        title, _ = program_calendar_summary(progs[0])
        return title, " · ".join(labels)
    return "多組別", " · ".join(labels[:4])


def program_calendar_summary(prog: dict) -> tuple[str, str]:
    """Short title + specs for calendar cells."""
    tp = safe_str(prog.get("type"))
    if tp == "比賽":
        return "比賽", ""
    if tp == "休息":
        return "休息", ""
    detail = workout_detail(prog)
    if detail:
        first = detail.split("\n")[0].strip()
        return first[:12], detail.split("\n")[0][:18]
    title = safe_str(prog.get("title")) or tp or "—"
    specs = program_specs(prog)
    if specs == title or specs == "-":
        specs = tp
    return title[:12], specs[:18]


def whatsapp_program_text(prog: dict, per: dict) -> str:
    from utils.config import APP_NAME, COACH_NAME
    phase = prog.get("phase") or per.get("global_phase", "")
    theme = prog.get("week_theme") or per.get("global_week_theme", "")
    detail = workout_detail(prog)
    detail_block = f"\n📝 {detail}\n" if detail else ""
    return (
        f"🏃 {APP_NAME} 訓練課表\n"
        f"📅 {prog['date']}\n"
        f"📋 {prog.get('type')} · {prog.get('group')}\n"
        f"{detail_block}"
        f"📊 階段:{phase} | 主題:{theme}\n"
        f"💡 {prog.get('tips') or '依教練指示'}\n"
        f"— {COACH_NAME}教練"
    )


def weekly_summary_text(athlete: str, logs, attendance, pbs, acwr: float, per: dict) -> str:
    from utils.config import APP_NAME, COACH_NAME
    lines = [
        f"【{APP_NAME} 每週訓練摘要】",
        f"學員：{athlete}",
        f"教練：{COACH_NAME}",
        "",
        f"📊 ACWR: {acwr:.2f}" + (" (偏高，注意恢復)" if acwr > 1.3 else ""),
        f"📅 階段：{per.get('global_phase')} · 主題：{per.get('global_week_theme')}",
        "",
        "🏃 近7次訓練：",
    ]
    for _, row in logs.head(7).iterrows():
        lines.append(f"  {row['date']} {row.get('train_type', row.get('event', ''))} RPE{row['rpe']} Load{row.get('load', '-')}")
    present = len(attendance[attendance["status"] == "present"]) if not attendance.empty else 0
    total = len(attendance) if not attendance.empty else 0
    lines.append(f"✅ 出席：{present}/{total}")
    if not pbs.empty:
        lines.append("🏆 近期成績：")
        for _, p in pbs.head(3).iterrows():
            lines.append(f"  {p['item']} {p['score']} ({p.get('comp_name') or p['date']})")
    lines += ["", f"— {APP_NAME} {COACH_NAME}教練"]
    return "\n".join(lines)
