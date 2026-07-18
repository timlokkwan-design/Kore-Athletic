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


def parse_workout_volume(text: str) -> dict[str, int]:
    """Parse free-text workout plan → total meters and rep count (e.g. 6×200m + 800m)."""
    import re

    blob = safe_str(text)
    total_meters = 0
    total_reps = 0
    if not blob:
        return {"total_meters": 0, "total_reps": 0}

    consumed: list[tuple[int, int]] = []
    mult_pat = re.compile(r"(\d+)\s*[×xX*]\s*(\d+)\s*(?:m|米)\b", re.I)
    for match in mult_pat.finditer(blob):
        reps, dist = int(match.group(1)), int(match.group(2))
        total_reps += reps
        total_meters += reps * dist
        consumed.append(match.span())

    def _inside_consumed(index: int) -> bool:
        return any(start <= index < end for start, end in consumed)

    single_pat = re.compile(r"\b(\d{2,5})\s*(?:m|米)\b", re.I)
    for match in single_pat.finditer(blob):
        if _inside_consumed(match.start(1)):
            continue
        dist = int(match.group(1))
        total_reps += 1
        total_meters += dist

    return {"total_meters": total_meters, "total_reps": total_reps}


def format_meters_short(meters: int) -> str:
    """Compact volume label for calendar cells, e.g. 2800 -> 2.8k."""
    m = max(0, int(meters or 0))
    if m == 0:
        return ""
    if m >= 10000:
        return f"{m // 1000}k"
    if m >= 1000:
        v = m / 1000
        text = f"{v:.1f}k"
        if text.endswith(".0k"):
            text = f"{int(v)}k"
        return text
    return f"{m}m"


def program_total_meters(prog: dict) -> int:
    """Run volume for one group row only (never sums multi-group merged cells)."""
    if prog.get("_programs"):
        return 0
    return workout_volume_from_program(prog)["total_meters"]


def workout_volume_from_program(prog: dict) -> dict[str, int]:
    """Volume from free-text plan, or legacy sets/reps/dist columns."""
    detail = workout_detail(prog)
    vol = parse_workout_volume(detail)
    if vol["total_meters"] > 0:
        return vol
    sets, reps, dist = safe_int(prog.get("sets")), safe_int(prog.get("reps")), safe_int(prog.get("dist"))
    if sets and reps and dist:
        total_reps = sets * reps
        return {"total_meters": total_reps * dist, "total_reps": total_reps}
    if reps and dist:
        return {"total_meters": reps * dist, "total_reps": reps}
    if dist:
        return {"total_meters": dist, "total_reps": 1}
    return vol


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


def has_time_venue(prog: dict) -> bool:
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    if start or end:
        return True
    venue = safe_str(prog.get("venue"))
    if venue and venue != "其他":
        return True
    if venue == "其他" and safe_str(prog.get("venue_other")):
        return True
    return False


def has_workout_plan(prog: dict) -> bool:
    from utils.config import normalize_train_type

    tp = normalize_train_type(safe_str(prog.get("type")))
    if tp in ("休息", "比賽"):
        return True
    if tp == "待排課":
        return False
    return bool(workout_detail(prog).strip())


def program_sync_status(prog: dict) -> str:
    """complete | need_workout | need_schedule | need_both | rest | empty"""
    from utils.config import normalize_train_type

    if not prog:
        return "empty"
    tp = normalize_train_type(safe_str(prog.get("type")))
    if tp == "休息":
        return "rest"
    tv = has_time_venue(prog)
    wp = has_workout_plan(prog)
    if wp and tv:
        return "complete"
    if tv and not wp:
        return "need_workout"
    if wp and not tv:
        return "need_schedule"
    return "need_both"


def day_sync_status(prog: dict | None) -> str:
    """Aggregate sync status for one calendar day (may merge multi-group)."""
    if not prog:
        return "empty"
    progs = prog.get("_programs") or [prog]
    statuses = [
        program_sync_status(p)
        for p in progs
        if program_sync_status(p) not in ("empty", "rest")
    ]
    if not statuses:
        return "rest" if prog else "empty"
    if any(s == "need_workout" for s in statuses):
        return "need_workout"
    if any(s == "need_schedule" for s in statuses):
        return "need_schedule"
    if any(s == "need_both" for s in statuses):
        return "need_both"
    return "complete"


def sync_status_label(status: str) -> str:
    return {
        "need_workout": "⚠️ 時間已定，待寫跑案",
        "need_schedule": "⚠️ 跑案已寫，待填時間地點",
        "need_both": "⚠️ 待寫跑案及時間地點",
        "complete": "✅ 課表完整",
    }.get(status, "")


def sync_status_priority(status: str) -> int:
    return {
        "need_workout": 0,
        "need_schedule": 1,
        "need_both": 2,
        "complete": 3,
        "rest": 4,
        "empty": 5,
    }.get(status, 9)


def format_time_venue_line(prog: dict) -> str:
    start = safe_str(prog.get("start_time"))
    end = safe_str(prog.get("end_time"))
    time_text = f"{start} – {end}" if start and end else (start or end or "")
    venue = resolve_venue(prog)
    parts = [p for p in (time_text, venue) if p and p not in ("（待設定）", "（待通知）")]
    return " · ".join(parts)


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
    from utils.config import group_display_label

    return group_display_label(group)


def _calendar_items(prog: dict | None = None, *, progs: list[dict] | None = None) -> list[dict]:
    items: list[dict] = list(progs) if progs else []
    if not items and prog:
        nested = prog.get("_programs")
        items = list(nested) if nested else [prog]
    return items


def _program_calendar_tone(prog: dict) -> str:
    """Per program: competition | training | rest | empty."""
    from utils.config import normalize_train_type

    if not prog:
        return "empty"
    tp = normalize_train_type(safe_str(prog.get("type")))
    if tp == "休息":
        return "rest"
    if tp == "比賽":
        return "competition"
    if has_time_venue(prog) or bool(workout_detail(prog).strip()):
        return "training"
    return "empty"


def calendar_cell_tone(prog: dict | None = None, *, progs: list[dict] | None = None) -> str:
    """Button tone: competition | training | rest | empty."""
    items = _calendar_items(prog, progs=progs)
    if not items:
        return "empty"
    tones = [_program_calendar_tone(p) for p in items]
    if "competition" in tones:
        return "competition"
    if "training" in tones:
        return "training"
    if all(t == "rest" for t in tones):
        return "rest"
    return "empty"


def calendar_cell_bg(prog: dict | None = None, *, progs: list[dict] | None = None) -> str:
    """Blue = training (time or content), red = competition, gray = rest / empty."""
    from utils.config import (
        CALENDAR_BG_COMPETITION,
        CALENDAR_BG_EMPTY,
        CALENDAR_BG_REST,
        CALENDAR_BG_TRAINING,
    )

    tone = calendar_cell_tone(prog, progs=progs)
    return {
        "competition": CALENDAR_BG_COMPETITION,
        "training": CALENDAR_BG_TRAINING,
        "rest": CALENDAR_BG_REST,
        "empty": CALENDAR_BG_EMPTY,
    }.get(tone, CALENDAR_BG_EMPTY)


def calendar_day_has_training(prog: dict | None = None, *, progs: list[dict] | None = None) -> bool:
    """True when the day has training or competition (not rest / empty)."""
    return calendar_cell_tone(prog, progs=progs) in ("training", "competition")


def calendar_day_event_chips(
    prog: dict | None = None,
    *,
    progs: list[dict] | None = None,
    max_chips: int = 2,
) -> tuple[list[dict], int]:
    """
    TimeTree-style chips for one calendar day.
    Each chip: {label, tone} where tone is training | competition | rest | empty.
    Returns (visible_chips, hidden_count).
    """
    from utils.config import normalize_train_type

    items = _calendar_items(prog, progs=progs)
    if not items:
        return [], 0

    chips: list[dict] = []
    for p in items:
        tone = _program_calendar_tone(p)
        tp = normalize_train_type(safe_str(p.get("type")))
        title, detail = program_calendar_summary(p)
        if tp == "休息":
            label = "休息"
        elif tp == "比賽":
            label = title or short_group_label(p.get("group")) or "比賽"
        elif tone == "empty":
            label = title or short_group_label(p.get("group")) or "待排"
        else:
            bit = detail.split("·")[0].strip() if detail else ""
            label = title or "訓練"
            if bit and bit not in label:
                label = f"{label} {bit}"
        label = label.replace("\n", " ").strip()[:14]
        chips.append({"label": label, "tone": tone})

    if not chips:
        return [], 0
    if all(c["tone"] == "rest" for c in chips) and len(chips) == 1:
        return chips[:max_chips], 0
    active = [c for c in chips if c["tone"] != "rest"]
    display = active if active else chips
    extra = max(0, len(display) - max_chips)
    return display[:max_chips], extra


def merge_programs_calendar_summary(progs: list[dict]) -> tuple[str, str]:
    """Multi-group day: per-group volume labels (not summed)."""
    from utils.config import normalize_train_type

    if not progs:
        return "", ""
    if len(progs) == 1:
        return program_calendar_summary(progs[0])
    types = [normalize_train_type(safe_str(p.get("type"))) for p in progs]
    if all(t == "休息" for t in types):
        return "休息", ""
    if any(t == "比賽" for t in types):
        return "比賽", ""
    active = [
        p for p in progs
        if normalize_train_type(safe_str(p.get("type"))) not in ("休息", "比賽")
    ]
    parts: list[str] = []
    for p in active:
        gl = short_group_label(p.get("group"))
        vol = format_meters_short(workout_volume_from_program(p)["total_meters"])
        parts.append(f"{gl}{vol}" if vol else gl)
    title = "·".join(parts[:4]) if parts else "訓練"
    times = [format_time_venue_line(p) for p in active if format_time_venue_line(p)]
    detail = " · ".join(dict.fromkeys(times[:3]))
    return title, detail


def program_calendar_summary(prog: dict) -> tuple[str, str]:
    """Calendar cell: group name + per-group volume (no train-type category)."""
    tp = safe_str(prog.get("type"))
    group_title = short_group_label(prog.get("group"))
    if tp == "比賽":
        return "比賽", group_title
    if tp == "休息":
        return "休息", ""
    if tp == "待排課":
        tv = format_time_venue_line(prog)
        return group_title or "待寫跑案", tv or "時間已定"
    vol = format_meters_short(workout_volume_from_program(prog)["total_meters"])
    detail = workout_detail(prog)
    spec = detail.split("\n")[0].strip()[:18] if detail else ""
    if vol:
        return group_title or "訓練", vol if not spec else f"{vol} · {spec}"
    if detail:
        first = detail.split("\n")[0].strip()
        return group_title or "訓練", first[:18]
    return group_title or "訓練", spec


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
