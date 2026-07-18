"""Full V6 data persistence — all CSV collections."""

from __future__ import annotations

import json
import uuid
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from utils.acwr import calc_load
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
    TRAIN_TYPES,
    USERS_FILE,
    VIDEOS_FILE,
    WELLNESS_FILE,
    default_program,
    normalize_group,
    normalize_train_type,
    schedule_placeholder_program,
)
from utils.helpers import format_birth_display, get_grade, is_missing, is_wind_valid, normalize_date_str, safe_float, safe_int, safe_str

PROGRAM_COLUMNS = [
    "date", "type", "title", "group", "sets", "reps", "dist", "rest",
    "duration", "rpe", "tips", "phase", "week_theme", "target_seconds", "load",
    "exercises", "tech_focus", "field_event", "attempts",
    "start_time", "end_time", "venue", "venue_other",
]
LOG_COLUMNS = [
    "id", "date", "student_name", "event", "rep_number", "target_seconds",
    "actual_seconds", "rpe", "injury_notes", "submitted_at", "duration", "load",
    "train_type", "remark", "laps_text", "avg_pace", "reaction", "kick",
    "hurdle_rhythm", "hurdle_count", "field_best", "field_attempts", "strength_note", "tech_notes",
]
USER_COLUMNS = [
    "username", "name", "role", "password", "specialty", "phone", "child_name",
    "school", "emergency_contact", "emergency_phone", "health", "gender",
    "name_en", "birth_year", "birth_date", "hkaaa_id", "hk_permanent_resident", "avatar",
]
WELLNESS_COLUMNS = ["id", "date", "athlete_name", "sleep", "soreness", "mood", "sick"]
PERIOD_COLUMNS = ["global_phase", "global_week_theme", "comp_target_date"]
ATTENDANCE_COLUMNS = ["date", "athlete_name", "status", "detail", "duration_minutes"]
INJURY_COLUMNS = ["id", "athlete_name", "body_part", "date", "diagnosis", "rehab", "restrict", "alt_training"]
COMP_COLUMNS = [
    "id", "name", "date", "event", "location", "registered",
    "deadline", "assembly_time", "transport", "notes", "published", "link",
]
COMP_ENTRY_COLUMNS = ["id", "comp_id", "athlete_name", "username", "events", "pbs_json", "submitted_at"]
VIDEO_COLUMNS = ["id", "athlete_name", "url", "timestamp", "notes", "issue", "date"]
TEMPLATE_COLUMNS = ["id"] + [c for c in PROGRAM_COLUMNS if c != "date"]
PENDING_COLUMNS = ["id", "athlete_name", "item", "score", "wind", "comp_name", "date"]
PENDING_SPECIALTY_COLUMNS = [
    "id", "username", "name", "current_specialty", "requested_specialty", "reason", "date",
]
RACE_COLUMNS = ["id", "athlete_name", "item", "score", "date", "wind", "comp_name", "grade", "valid"]

TEST_USERNAMES = frozenset({"student1", "student2", "student3", "parent1"})
TEST_STUDENT_NAMES = frozenset({"陳大文", "林明美", "張豪傑", "陳家長"})


def _data_path(filename: str) -> Path:
    base = Path(__file__).resolve().parent.parent / DATA_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / filename


def _ensure_cols(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]


def _read(filename: str, columns: list[str]) -> pd.DataFrame:
    from utils.session_cache import cached_dataframe

    def _load() -> pd.DataFrame:
        from utils.supabase_config import is_supabase_enabled

        if is_supabase_enabled():
            from utils.supabase_io import read_csv_table
            return read_csv_table(filename, columns)
        path = _data_path(filename)
        if not path.exists():
            return pd.DataFrame(columns=columns)
        return _ensure_cols(pd.read_csv(path), columns)

    return cached_dataframe(filename, _load)


def _write(filename: str, df: pd.DataFrame, columns: list[str]) -> None:
    from utils.session_cache import invalidate_data_cache
    from utils.supabase_config import is_supabase_enabled

    if is_supabase_enabled():
        from utils.supabase_io import write_csv_table
        write_csv_table(filename, df, columns)
        invalidate_data_cache()
        return
    _ensure_cols(df, columns).to_csv(_data_path(filename), index=False, encoding="utf-8-sig")
    invalidate_data_cache()


def _next_id(df: pd.DataFrame, col: str = "id") -> int:
    if df.empty or col not in df.columns or pd.isna(df[col].max()):
        return 1
    return int(df[col].max()) + 1


def _uid() -> str:
    return uuid.uuid4().hex[:10]


# ── Programs ────────────────────────────────────────────────────────────────

def load_programs() -> pd.DataFrame:
    df = _read(PROGRAMS_FILE, PROGRAM_COLUMNS)
    if not df.empty and df["type"].astype(str).eq("田賽").any():
        df = df.copy()
        df.loc[df["type"].astype(str) == "田賽", "type"] = "比賽"
        save_programs(df)
    return df


def save_programs(df: pd.DataFrame) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    _write(PROGRAMS_FILE, df, PROGRAM_COLUMNS)


def _clean_str(v, default: str = "") -> str:
    return safe_str(v, default)


def _row_to_program(row) -> dict:
    return {
        "date": safe_str(row["date"]),
        "type": normalize_train_type(safe_str(row.get("type"), "間歇跑")),
        "title": safe_str(row.get("title")), "group": normalize_group(safe_str(row.get("group"), "短跑組")),
        "sets": safe_int(row.get("sets")), "reps": safe_int(row.get("reps")), "dist": safe_int(row.get("dist")),
        "rest": safe_str(row.get("rest")), "duration": safe_int(row.get("duration"), 60),
        "rpe": safe_int(row.get("rpe"), 7), "tips": safe_str(row.get("tips")),
        "phase": safe_str(row.get("phase")), "week_theme": safe_str(row.get("week_theme")),
        "target_seconds": safe_float(row.get("target_seconds")),
        "load": safe_int(row.get("load")), "exercises": safe_str(row.get("exercises")),
        "tech_focus": safe_str(row.get("tech_focus")), "field_event": safe_str(row.get("field_event"), "跳遠"),
        "attempts": safe_int(row.get("attempts"), 10),
        "start_time": safe_str(row.get("start_time")),
        "end_time": safe_str(row.get("end_time")),
        "venue": safe_str(row.get("venue")),
        "venue_other": safe_str(row.get("venue_other")),
    }


def row_to_program(row) -> dict:
    """Public helper for calendar/grid views."""
    return _row_to_program(row)


def ensure_program_dict(raw) -> dict:
    """Always return a plain program dict — never a pandas Series."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, pd.Series):
        return _row_to_program(raw)
    return {}


def get_programs_for_date(for_date: date | str) -> list[dict]:
    """All program rows for one calendar date (multiple groups allowed)."""
    if isinstance(for_date, date):
        target = for_date.isoformat()
    else:
        target = normalize_date_str(for_date)
    programs = load_programs()
    if programs.empty or not target:
        return []
    match = programs[programs["date"].astype(str).str[:10] == target]
    return [_row_to_program(row) for _, row in match.iterrows()]


def pick_program_for_student(programs: list[dict], specialty: str | None = None) -> dict | None:
    """Prefer group-specific program; fall back to 全體組員."""
    if not programs:
        return None
    if not specialty:
        return programs[0]
    specific = None
    general = None
    for p in programs:
        group = normalize_group(safe_str(p.get("group")))
        if group == "全體組員":
            general = general or p
        elif program_visible_to_student(p, specialty):
            specific = p
    return specific or general


def get_program(
    for_date: date | None = None,
    *,
    group: str | None = None,
    specialty: str | None = None,
) -> dict:
    target = normalize_date_str((for_date or date.today()).isoformat())
    day_programs = get_programs_for_date(target)
    if group:
        for p in day_programs:
            if safe_str(p.get("group")) == group:
                return p
        fallback = default_program(target)
        fallback["group"] = group
        return fallback
    if specialty:
        picked = pick_program_for_student(day_programs, specialty)
        if picked:
            return picked
    if day_programs:
        return day_programs[0]
    return default_program(target)


def get_today_menu(for_date: date | None = None, specialty: str | None = None) -> dict:
    from utils.helpers import program_specs
    p = get_program(for_date, specialty=specialty)
    return {**p, "event": p.get("title") or p.get("type", ""), "description": program_specs(p), "notes": p.get("tips", "")}


def save_program(prog: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    prog = dict(prog)
    train_type = prog.get("type", "間歇跑")
    rpe = float(prog.get("rpe") or 7)
    sets = int(prog.get("sets") or 0)
    reps = int(prog.get("reps") or 0)
    dist = int(prog.get("dist") or 0)
    duration = float(prog.get("duration") or 0)
    if sets > 0 and reps > 0 and dist > 0:
        total_meters = 0
    elif dist > 0 and safe_str(prog.get("rest")):
        total_meters = dist
    else:
        total_meters = 0
    if duration <= 0 and total_meters > 0:
        from utils.acwr import estimate_workout_minutes
        duration = estimate_workout_minutes(total_meters, str(train_type))
        prog["duration"] = int(round(duration))
    prog["load"] = calc_load(
        train_type,
        duration or 45,
        rpe,
        sets,
        reps,
        dist if sets > 0 else 0,
        total_meters=total_meters,
    )
    programs = load_programs()
    target = normalize_date_str(prog["date"])
    prog["date"] = target
    prog["group"] = normalize_group(safe_str(prog.get("group"), "短跑組"))
    if not safe_str(prog.get("title")):
        prog["title"] = safe_str(prog.get("type"))
    if programs.empty:
        save_programs(pd.DataFrame([prog]))
        return
    mask = (
        programs["date"].astype(str).str[:10] == target
    ) & (programs["group"].astype(str) == prog["group"])
    idx = programs.index[mask].tolist()
    row = pd.DataFrame([prog])
    if idx:
        programs = programs.drop(index=idx)
    programs = pd.concat([programs, row], ignore_index=True)
    save_programs(programs)


def program_exists(for_date: date | str) -> bool:
    target = normalize_date_str(for_date.isoformat() if isinstance(for_date, date) else for_date)
    programs = load_programs()
    if programs.empty:
        return False
    return not programs[programs["date"].astype(str).str[:10] == target].empty


def delete_program(for_date: date | str, group: str | None = None) -> bool:
    """Remove program(s) for a date. With group, only that row is removed."""
    from utils.permissions import enforce_coach_if_logged_in

    enforce_coach_if_logged_in()
    target = normalize_date_str(for_date.isoformat() if isinstance(for_date, date) else str(for_date))
    if not target:
        return False
    if group:
        programs = load_programs()
        if programs.empty:
            return False
        mask = (
            programs["date"].astype(str).str[:10] == target
        ) & (programs["group"].astype(str) == group)
        removed = int(mask.sum())
        if not removed:
            return False
        save_programs(programs[~mask].reset_index(drop=True))
        return True
    return delete_programs([target]) > 0


def delete_programs(dates: list[str] | list[date]) -> int:
    """Remove saved programs for multiple dates. Returns number of rows deleted."""
    from utils.permissions import enforce_coach_if_logged_in

    enforce_coach_if_logged_in()
    if not dates:
        return 0
    targets = {
        normalize_date_str(d.isoformat() if isinstance(d, date) else str(d))
        for d in dates
    }
    targets.discard("")
    if not targets:
        return 0
    programs = load_programs()
    if programs.empty:
        return 0
    mask = programs["date"].astype(str).str[:10].isin(targets)
    removed = int(mask.sum())
    if not removed:
        return 0
    save_programs(programs[~mask].reset_index(drop=True))
    return removed


def _copy_payloads(source_date: str, prog: dict | list[dict] | None) -> list[dict]:
    src = normalize_date_str(source_date)
    if isinstance(prog, list):
        return [dict(p) for p in prog if p]
    if prog is not None:
        return [dict(prog)]
    return [dict(p) for p in get_programs_for_date(src)]


def copy_program(source_date: str, target_date: str, prog: dict | list[dict] | None = None) -> bool:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    """Copy all group programs (or one payload) to another date."""
    src = normalize_date_str(source_date)
    tgt = normalize_date_str(target_date)
    if not src or not tgt or src == tgt:
        return False
    payloads = _copy_payloads(src, prog)
    if not payloads:
        return False
    for data in payloads:
        data["date"] = tgt
        save_program(data)
    return True


def copy_program_to_dates(source_date: str, target_dates: list[str], prog: dict | list[dict] | None = None) -> int:
    """Copy all group programs on source date to multiple target dates."""
    src = normalize_date_str(source_date)
    payloads = _copy_payloads(src, prog)
    if not payloads:
        return 0
    count = 0
    for tgt in target_dates:
        t = normalize_date_str(tgt)
        if not t or t == src:
            continue
        for data in payloads:
            row = dict(data)
            row["date"] = t
            save_program(row)
        count += 1
    return count


def build_coach_prog_map(programs: pd.DataFrame) -> dict[str, dict]:
    """One calendar cell per date; multi-group days show combined summary."""
    from utils.helpers import merge_programs_calendar_summary

    if programs.empty:
        return {}
    by_date: dict[str, list[dict]] = {}
    for _, row in programs.iterrows():
        ds = normalize_date_str(row.get("date"))
        if not ds:
            continue
        by_date.setdefault(ds, []).append(_row_to_program(row))
    result: dict[str, dict] = {}
    for ds, progs in by_date.items():
        if len(progs) == 1:
            result[ds] = progs[0]
            continue
        title, spec = merge_programs_calendar_summary(progs)
        merged = dict(progs[0])
        merged["title"] = title
        non_rest = [
            p for p in progs
            if normalize_train_type(safe_str(p.get("type"))) != "休息"
        ]
        types = {normalize_train_type(safe_str(p.get("type"))) for p in non_rest}
        if len(types) == 1:
            merged["type"] = next(iter(types))
        elif non_rest:
            merged["type"] = normalize_train_type(safe_str(non_rest[0].get("type")))
        merged["_multi"] = True
        merged["_programs"] = progs
        if spec:
            merged["tips"] = spec
        result[ds] = merged
    return result


def build_student_prog_map(programs: pd.DataFrame, specialty: str) -> dict[str, dict]:
    """One program per date, matched to student specialty."""
    if programs.empty:
        return {}
    by_date: dict[str, list[dict]] = {}
    for _, row in programs.iterrows():
        ds = normalize_date_str(row.get("date"))
        if not ds:
            continue
        by_date.setdefault(ds, []).append(_row_to_program(row))
    result: dict[str, dict] = {}
    for ds, progs in by_date.items():
        picked = pick_program_for_student(progs, specialty)
        if picked:
            result[ds] = picked
    return result


def get_programs_for_month(year: int, month: int) -> pd.DataFrame:
    programs = load_programs()
    if programs.empty:
        return programs
    prefix = f"{year}-{month:02d}"
    return programs[programs["date"].astype(str).str[:10].str.startswith(prefix)]


def filter_programs_by_group(programs: pd.DataFrame, group: str | None) -> pd.DataFrame:
    """Filter month programs to one training group (None = show all)."""
    if programs.empty or not group:
        return programs
    target = normalize_group(group)
    mask = programs["group"].astype(str).map(normalize_group) == target
    return programs[mask]


def apply_recovery_template(start_date: date) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    types = ["恢復跑", "恢復跑", "技術課", "節奏跑", "間歇跑"]
    for i, tp in enumerate(types, 1):
        dt = (start_date + timedelta(days=i)).isoformat()
        dur, rpe = 30 + i * 10, 3 + i
        save_program({
            "date": dt, "type": tp, "title": f"賽後恢復 D{i}", "group": "全體組員",
            "sets": 0, "reps": 0, "dist": 0, "rest": "", "duration": dur, "rpe": rpe,
            "tips": "賽後恢復範本", "phase": "", "week_theme": "", "target_seconds": 0,
            "exercises": "", "tech_focus": "", "field_event": "", "attempts": 0,
        })


# ── Templates ───────────────────────────────────────────────────────────────

def load_templates() -> pd.DataFrame:
    return _read(TEMPLATES_FILE, TEMPLATE_COLUMNS)


def save_templates(df: pd.DataFrame) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    _write(TEMPLATES_FILE, df, TEMPLATE_COLUMNS)


def save_as_template(prog: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_templates()
    row = {k: prog.get(k, "") for k in TEMPLATE_COLUMNS if k != "id"}
    row["id"] = _uid()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_templates(df)


def apply_template(template_id: str, target_date: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_templates()
    match = df[df["id"].astype(str) == template_id]
    if match.empty:
        return
    prog = match.iloc[0].to_dict()
    prog["date"] = target_date
    save_program(prog)


def delete_template(template_id: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_templates()
    df = df[df["id"].astype(str) != str(template_id)]
    save_templates(df)


# ── Periodization ───────────────────────────────────────────────────────────

def load_periodization() -> dict:
    df = _read(PERIOD_FILE, PERIOD_COLUMNS)
    if df.empty:
        return DEFAULT_PERIODIZATION.copy()
    row = df.iloc[0]
    return {
        "global_phase": str(row.get("global_phase") or DEFAULT_PERIODIZATION["global_phase"]),
        "global_week_theme": str(row.get("global_week_theme") or DEFAULT_PERIODIZATION["global_week_theme"]),
        "comp_target_date": str(row.get("comp_target_date") or DEFAULT_PERIODIZATION["comp_target_date"]),
    }


def save_periodization(data: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    _write(PERIOD_FILE, pd.DataFrame([data]), PERIOD_COLUMNS)


def days_until_competition() -> int | None:
    target = load_periodization().get("comp_target_date")
    if not target:
        return None
    try:
        return (date.fromisoformat(str(target)) - date.today()).days
    except ValueError:
        return None


# ── Timetable (time & venue on calendar programs) ───────────────────────────

def program_visible_to_student(prog: dict, specialty: str) -> bool:
    from utils.config import SPECIALTY_TO_GROUP, normalize_group

    group = normalize_group(safe_str(prog.get("group")))
    if group == "全體組員":
        return True
    return group == SPECIALTY_TO_GROUP.get(safe_str(specialty), "")


def save_program_time_venue(
    date_str: str,
    start_time: str,
    end_time: str,
    venue: str,
    venue_other: str = "",
    *,
    group: str = "",
) -> None:
    target = normalize_date_str(date_str)
    updates = {
        "start_time": safe_str(start_time),
        "end_time": safe_str(end_time),
        "venue": safe_str(venue),
        "venue_other": safe_str(venue_other) if venue == "其他" else "",
    }
    day_programs = get_programs_for_date(target)
    if not day_programs:
        prog = schedule_placeholder_program(target, group=group or "短跑組")
        prog.update(updates)
        save_program(prog)
        return
    for prog in day_programs:
        merged = dict(prog)
        merged.update(updates)
        if normalize_train_type(safe_str(merged.get("type"))) == "休息":
            merged["type"] = "待排課"
            merged["title"] = "時間已定"
        save_program(merged)


def _program_exists_on_date(date_str: str) -> bool:
    target = normalize_date_str(date_str)
    programs = load_programs()
    if programs.empty:
        return False
    return target in programs["date"].astype(str).str[:10].tolist()


def is_training_day(date_str: str) -> bool:
    """True if date has a non-rest, non-placeholder program in the calendar."""
    target = normalize_date_str(date_str)
    if not _program_exists_on_date(target):
        return False
    for prog in get_programs_for_date(target):
        tp = normalize_train_type(safe_str(prog.get("type")))
        if tp not in ("休息", "待排課"):
            return True
    return False


def has_schedule_slot(date_str: str) -> bool:
    """True if any program on this date has time or venue set."""
    from utils.helpers import has_time_venue

    target = normalize_date_str(date_str)
    for prog in get_programs_for_date(target):
        if has_time_venue(prog):
            return True
    return False


def copy_time_venue_to_dates(source_date: str, target_dates: list[str]) -> int:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    """Copy time/venue from source to multiple dates. Returns success count."""
    src = normalize_date_str(source_date)
    src_programs = get_programs_for_date(src)
    ref = src_programs[0] if src_programs else get_program(date.fromisoformat(src))
    payload = {
        "start_time": safe_str(ref.get("start_time")),
        "end_time": safe_str(ref.get("end_time")),
        "venue": safe_str(ref.get("venue")),
        "venue_other": safe_str(ref.get("venue_other")),
    }
    count = 0
    for tgt in target_dates:
        t = normalize_date_str(tgt)
        if not t or t == src:
            continue
        save_program_time_venue(t, **payload)
        count += 1
    return count


def apply_time_venue_to_dates(
    target_dates: list[str],
    start_time: str,
    end_time: str,
    venue: str,
    venue_other: str = "",
) -> int:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    count = 0
    for tgt in target_dates:
        t = normalize_date_str(tgt)
        if not t:
            continue
        save_program_time_venue(t, start_time, end_time, venue, venue_other)
        count += 1
    return count


def get_timetable_entries(
    *,
    specialty: str | None = None,
    from_date: date | None = None,
    days_ahead: int = 60,
    include_rest: bool = False,
) -> list[dict]:
    start = from_date or date.today()
    end = start + timedelta(days=days_ahead)
    programs = load_programs()
    if programs.empty:
        return []
    by_date: dict[str, list[dict]] = {}
    for _, row in programs.iterrows():
        ds = normalize_date_str(row.get("date"))
        if not ds:
            continue
        try:
            d = date.fromisoformat(ds)
        except ValueError:
            continue
        if d < start or d > end:
            continue
        by_date.setdefault(ds, []).append(_row_to_program(row))

    entries: list[dict] = []
    for ds in sorted(by_date.keys()):
        prog = pick_program_for_student(by_date[ds], specialty) if specialty else by_date[ds][0]
        if not prog:
            continue
        if not include_rest and prog.get("type") == "休息":
            continue
        if not include_rest and normalize_train_type(safe_str(prog.get("type"))) == "待排課":
            from utils.helpers import has_time_venue
            if not has_time_venue(prog):
                continue
        entries.append(prog)
    return entries


# ── Users ───────────────────────────────────────────────────────────────────

def load_users() -> pd.DataFrame:
    df = _read(USERS_FILE, USER_COLUMNS)
    if "password" in df.columns:
        df["password"] = df["password"].astype(str).replace({"nan": "", "None": ""})
    return df


def save_users(df: pd.DataFrame) -> None:
    _write(USERS_FILE, df, USER_COLUMNS)


def get_user(username: str) -> dict | None:
    users = load_users()
    if users.empty:
        return None
    for col in ("username", "name"):
        match = users[users[col].astype(str) == username]
        if not match.empty:
            return match.iloc[0].to_dict()
    return None


def register_user(data: dict) -> None:
    from utils.passwords import hash_password

    users = load_users()
    data = {**data, "role": "pending"}
    plain = safe_str(data.get("password"))
    if plain:
        data["password"] = hash_password(plain)
    users = pd.concat([users, pd.DataFrame([data])], ignore_index=True)
    save_users(users)


def approve_student(username: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    users = load_users()
    mask = users["username"].astype(str) == username
    if mask.any():
        users.loc[mask, "role"] = "student"
        save_users(users)


def remove_student(username: str) -> None:
    """Remove student from active team (soft delete — keeps training history)."""
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    users = load_users()
    mask = users["username"].astype(str) == username
    if mask.any() and users.loc[mask, "role"].astype(str).eq("student").any():
        users.loc[mask, "role"] = "removed"
        save_users(users)


def get_students() -> list[dict]:
    users = load_users()
    return users[users["role"] == "student"].to_dict("records") if not users.empty else []


def get_student_names() -> list[str]:
    return [u["name"] for u in get_students()]


def set_user_password(username: str, plain_password: str) -> tuple[bool, str]:
    from utils.passwords import hash_password

    password = safe_str(plain_password)
    if len(password) < 3:
        return False, "密碼至少需要 3 個字元"
    users = load_users()
    mask = users["username"].astype(str) == username
    if not mask.any():
        return False, "找不到帳號"
    users.loc[mask, "password"] = hash_password(password)
    save_users(users)
    return True, "密碼已更新"


def update_user_profile(username: str, data: dict) -> None:
    from utils.permissions import enforce_self_username_if_logged_in

    enforce_self_username_if_logged_in(username)
    plain_password = safe_str(data.get("password"))
    if plain_password:
        ok, msg = set_user_password(username, plain_password)
        if not ok:
            raise ValueError(msg)
    users = load_users()
    mask = users["username"].astype(str) == username
    if not mask.any():
        return
    blocked = ("username", "role", "specialty", "child_name", "password")
    for key, value in data.items():
        if key in USER_COLUMNS and key not in blocked:
            users.loc[mask, key] = value
    save_users(users)


def reset_student_password(username: str, new_password: str) -> tuple[bool, str]:
    from utils.permissions import enforce_coach_if_logged_in

    enforce_coach_if_logged_in()
    users = load_users()
    mask = users["username"].astype(str) == username
    if not mask.any():
        return False, "找不到此學員"
    if users.loc[mask, "role"].astype(str).iloc[0] != "student":
        return False, "只能重設學員密碼"
    return set_user_password(username, new_password)


def get_user_by_name(name: str) -> dict | None:
    users = load_users()
    if users.empty:
        return None
    match = users[users["name"].astype(str) == name]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


AVATAR_MAX_BYTES = 2 * 1024 * 1024
AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AVATAR_MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def avatars_dir() -> Path:
    path = _data_path(AVATARS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_avatar_filename(username: str) -> str | None:
    user = get_user(username)
    if not user:
        return None
    stored = safe_str(user.get("avatar"))
    if stored:
        path = avatars_dir() / stored
        if path.exists():
            return stored
    for ext in AVATAR_EXTENSIONS:
        path = avatars_dir() / f"{username}{ext}"
        if path.exists():
            return path.name
    return None


def get_avatar_path(*, username: str | None = None, name: str | None = None) -> Path | None:
    if not username and name:
        user = get_user_by_name(name)
        username = safe_str(user.get("username")) if user else ""
    if not username:
        return None
    filename = get_avatar_filename(username)
    if not filename:
        return None
    return avatars_dir() / filename


def save_user_avatar(username: str, data: bytes, content_type: str) -> tuple[bool, str]:
    from utils.permissions import enforce_self_username_if_logged_in
    enforce_self_username_if_logged_in(username)
    if len(data) > AVATAR_MAX_BYTES:
        return False, "圖片大小不可超過 2MB"
    ext = AVATAR_MIME_EXT.get(content_type)
    if not ext:
        return False, "只支援 JPG、PNG、WEBP 格式"
    target_dir = avatars_dir()
    for old in target_dir.glob(f"{username}.*"):
        old.unlink(missing_ok=True)
    filename = f"{username}{ext}"
    (target_dir / filename).write_bytes(data)
    users = load_users()
    mask = users["username"].astype(str) == username
    if not mask.any():
        return False, "找不到此學員"
    users.loc[mask, "avatar"] = filename
    save_users(users)
    return True, "頭像已更新"


def remove_user_avatar(username: str) -> None:
    from utils.permissions import enforce_self_username_if_logged_in
    enforce_self_username_if_logged_in(username)
    for old in avatars_dir().glob(f"{username}.*"):
        old.unlink(missing_ok=True)
    users = load_users()
    mask = users["username"].astype(str) == username
    if mask.any():
        users.loc[mask, "avatar"] = ""
        save_users(users)


def get_pending_users() -> pd.DataFrame:
    users = load_users()
    return users[users["role"] == "pending"] if not users.empty else pd.DataFrame(columns=USER_COLUMNS)


def update_user_specialty(username: str, specialty: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    users = load_users()
    mask = users["username"].astype(str) == username
    if mask.any():
        users.loc[mask, "specialty"] = specialty
        save_users(users)


def load_pending_specialty() -> pd.DataFrame:
    return _read(PENDING_SPECIALTY_FILE, PENDING_SPECIALTY_COLUMNS)


def save_pending_specialty(df: pd.DataFrame) -> None:
    _write(PENDING_SPECIALTY_FILE, df, PENDING_SPECIALTY_COLUMNS)


def get_pending_specialty_for_user(username: str) -> dict | None:
    df = load_pending_specialty()
    if df.empty:
        return None
    match = df[df["username"].astype(str) == username]
    if match.empty:
        return None
    row = match.iloc[-1]
    return {
        "id": safe_str(row["id"]),
        "username": safe_str(row["username"]),
        "name": safe_str(row["name"]),
        "current_specialty": safe_str(row["current_specialty"]),
        "requested_specialty": safe_str(row["requested_specialty"]),
        "reason": safe_str(row["reason"]),
        "date": safe_str(row["date"]),
    }


def submit_specialty_change(
    username: str,
    name: str,
    current_specialty: str,
    requested_specialty: str,
    reason: str = "",
) -> tuple[bool, str]:
    from utils.permissions import PermissionDenied, require_self_username
    try:
        require_self_username(username)
    except PermissionDenied as exc:
        return False, exc.message
    if requested_specialty == current_specialty:
        return False, "新專項與目前專項相同"
    if get_pending_specialty_for_user(username):
        return False, "你已有待審批的專項更改申請"
    df = load_pending_specialty()
    df = df[df["username"].astype(str) != username]
    df = pd.concat([df, pd.DataFrame([{
        "id": _uid(),
        "username": username,
        "name": name,
        "current_specialty": current_specialty,
        "requested_specialty": requested_specialty,
        "reason": reason.strip(),
        "date": date.today().isoformat(),
    }])], ignore_index=True)
    save_pending_specialty(df)
    return True, ""


def approve_specialty_change(request_id: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_pending_specialty()
    match = df[df["id"].astype(str) == request_id]
    if match.empty:
        return
    row = match.iloc[0]
    update_user_specialty(safe_str(row["username"]), safe_str(row["requested_specialty"]))
    save_pending_specialty(df[df["id"].astype(str) != request_id])


def reject_specialty_change(request_id: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_pending_specialty()
    save_pending_specialty(df[df["id"].astype(str) != request_id])


# ── Logs ────────────────────────────────────────────────────────────────────

def load_logs() -> pd.DataFrame:
    return _read(LOGS_FILE, LOG_COLUMNS)


def save_logs(df: pd.DataFrame) -> None:
    _write(LOGS_FILE, df, LOG_COLUMNS)


def append_training_log(**kwargs) -> None:
    from utils.permissions import require_athlete_self
    student_name = kwargs["student_name"]
    require_athlete_self(safe_str(student_name))
    menu = kwargs.pop("menu", None) or get_today_menu()
    rpe = int(kwargs.get("rpe", 5))
    duration = int(kwargs.get("duration") or menu.get("duration") or 60)
    train_type = kwargs.get("train_type") or menu.get("type", "間歇跑")
    load = calc_load(train_type, duration, rpe, int(menu.get("sets") or 0),
                     int(menu.get("reps") or 0), int(menu.get("dist") or 0))
    logs = load_logs()
    record = {
        "id": _next_id(logs), "date": menu["date"], "student_name": student_name.strip(),
        "event": menu.get("title") or menu.get("event", ""), "train_type": train_type,
        "duration": duration, "load": load, "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
        **{k: v for k, v in kwargs.items() if k != "menu"},
    }
    record.setdefault("rep_number", 1)
    record.setdefault("target_seconds", float(menu.get("target_seconds") or 0))
    record.setdefault("actual_seconds", 0.0)
    record.setdefault("injury_notes", "無不適")
    record.setdefault("remark", "")
    save_logs(pd.concat([logs, pd.DataFrame([record])], ignore_index=True))


def get_logs_for_date(for_date: date | None = None) -> pd.DataFrame:
    target = (for_date or date.today()).isoformat()
    logs = load_logs()
    return logs[logs["date"].astype(str) == target].copy() if not logs.empty else logs


def get_all_logs() -> pd.DataFrame:
    return load_logs()


def get_logs_for_athlete(name: str) -> pd.DataFrame:
    logs = load_logs()
    return logs[logs["student_name"] == name].copy() if not logs.empty else logs


def filter_logs(
    date_str: str | None = None,
    rpe_range: str | None = None,
    student_name: str | None = None,
    *,
    exclude_test: bool = False,
) -> pd.DataFrame:
    logs = load_logs().sort_values("submitted_at", ascending=False) if not load_logs().empty else load_logs()
    if exclude_test and not logs.empty:
        logs = logs[~logs["student_name"].astype(str).isin(TEST_STUDENT_NAMES)]
    if date_str:
        logs = logs[logs["date"].astype(str) == date_str]
    if student_name:
        logs = logs[logs["student_name"].astype(str) == student_name]
    if rpe_range and "-" in rpe_range:
        lo, hi = map(int, rpe_range.split("-"))
        logs = logs[(logs["rpe"] >= lo) & (logs["rpe"] <= hi)]
    return logs


def log_completion_rate(for_date: date | None = None) -> int:
    athletes = get_student_names()
    if not athletes:
        return 0
    logged = get_logs_for_date(for_date)["student_name"].unique().tolist()
    return round(len(logged) / len(athletes) * 100)


# ── Wellness ────────────────────────────────────────────────────────────────

def load_wellness() -> pd.DataFrame:
    return _read(WELLNESS_FILE, WELLNESS_COLUMNS)


def save_wellness(df: pd.DataFrame) -> None:
    _write(WELLNESS_FILE, df, WELLNESS_COLUMNS)


def get_wellness(for_date: date | None = None, athlete: str | None = None) -> dict | None:
    target = (for_date or date.today()).isoformat()
    df = load_wellness()
    if df.empty:
        return None
    mask = df["date"].astype(str) == target
    if athlete:
        mask &= df["athlete_name"] == athlete
    match = df[mask]
    if match.empty:
        return None
    row = match.iloc[-1]
    return {"date": str(row["date"]), "athlete_name": str(row["athlete_name"]),
            "sleep": int(row["sleep"]), "soreness": int(row["soreness"]),
            "mood": int(row["mood"]), "sick": bool(row.get("sick"))}


def submit_wellness(athlete_name: str, sleep: int, soreness: int, mood: int, sick: bool) -> None:
    from utils.permissions import require_athlete_self
    require_athlete_self(athlete_name)
    df = load_wellness()
    target = date.today().isoformat()
    df = df[~((df["date"].astype(str) == target) & (df["athlete_name"] == athlete_name))]
    df = pd.concat([df, pd.DataFrame([{
        "id": _next_id(df), "date": target, "athlete_name": athlete_name,
        "sleep": sleep, "soreness": soreness, "mood": mood, "sick": sick,
    }])], ignore_index=True)
    save_wellness(df)


# ── Attendance ──────────────────────────────────────────────────────────────

def load_attendance() -> pd.DataFrame:
    return _read(ATTENDANCE_FILE, ATTENDANCE_COLUMNS)


def save_attendance(df: pd.DataFrame) -> None:
    _write(ATTENDANCE_FILE, df, ATTENDANCE_COLUMNS)


def check_in(athlete_name: str, duration_minutes: int = 0) -> None:
    from utils.permissions import require_athlete_self
    require_athlete_self(athlete_name)
    df = load_attendance()
    target = date.today().isoformat()
    df = df[~((df["date"].astype(str) == target) & (df["athlete_name"] == athlete_name))]
    df = pd.concat([df, pd.DataFrame([{
        "date": target, "athlete_name": athlete_name, "status": "present",
        "detail": pd.Timestamp.now().strftime("%H:%M:%S"),
        "duration_minutes": int(duration_minutes or 0),
    }])], ignore_index=True)
    save_attendance(df)


def get_attendance_record(athlete_name: str, date_str: str) -> dict | None:
    df = load_attendance()
    if df.empty:
        return None
    target = normalize_date_str(date_str)
    match = df[
        (df["date"].astype(str).str[:10] == target)
        & (df["athlete_name"].astype(str) == athlete_name)
    ]
    if match.empty:
        return None
    row = match.iloc[-1]
    return {
        "date": safe_str(row["date"]),
        "athlete_name": safe_str(row["athlete_name"]),
        "status": safe_str(row["status"]),
        "detail": safe_str(row["detail"]),
        "duration_minutes": safe_int(row.get("duration_minutes"), 0),
    }


def get_attendance_map_for_month(athlete_name: str, year: int, month: int) -> dict[str, dict]:
    df = load_attendance()
    if df.empty:
        return {}
    prefix = f"{year}-{month:02d}"
    sub = df[
        (df["athlete_name"].astype(str) == athlete_name)
        & (df["date"].astype(str).str[:7] == prefix)
    ]
    result: dict[str, dict] = {}
    for _, row in sub.iterrows():
        ds = normalize_date_str(row.get("date"))
        if ds:
            result[ds] = {
                "status": safe_str(row["status"]),
                "detail": safe_str(row["detail"]),
                "duration_minutes": safe_int(row.get("duration_minutes"), 0),
            }
    return result


def mark_leave(athlete_name: str, reason: str) -> None:
    from utils.permissions import require_athlete_self
    require_athlete_self(athlete_name)
    df = load_attendance()
    target = date.today().isoformat()
    df = df[~((df["date"].astype(str) == target) & (df["athlete_name"] == athlete_name))]
    df = pd.concat([df, pd.DataFrame([{
        "date": target, "athlete_name": athlete_name, "status": "leave", "detail": reason,
    }])], ignore_index=True)
    save_attendance(df)


def get_attendance_today() -> pd.DataFrame:
    df = load_attendance()
    target = date.today().isoformat()
    return df[df["date"].astype(str) == target] if not df.empty else df


def attendance_rate(athlete_name: str) -> int:
    df = load_attendance()
    if df.empty:
        return 0
    sub = df[df["athlete_name"] == athlete_name]
    if sub.empty:
        return 0
    return round(len(sub[sub["status"] == "present"]) / len(sub) * 100)


def get_attendance_for_month(year: int, month: int) -> pd.DataFrame:
    df = load_attendance()
    if df.empty:
        return df
    prefix = f"{year}-{month:02d}"
    return df[df["date"].astype(str).str[:7] == prefix].copy()


def get_week_range(reference: date | None = None) -> tuple[date, date]:
    from datetime import timedelta

    ref = reference or date.today()
    start = ref - timedelta(days=ref.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_attendance_for_week(reference: date | None = None) -> pd.DataFrame:
    start, end = get_week_range(reference)
    df = load_attendance()
    if df.empty:
        return df
    dates: set[str] = set()
    d = start
    from datetime import timedelta

    while d <= end:
        dates.add(d.isoformat())
        d += timedelta(days=1)
    return df[df["date"].astype(str).str[:10].isin(dates)].copy()


def attendance_status_symbol(status: str) -> str:
    if status == "present":
        return "✅"
    if status == "leave":
        return "📝"
    return "—"


def _attendance_cell(status: str, detail: str, duration_minutes: int) -> str:
    if status == "present":
        dur = int(duration_minutes or 0)
        return f"✅ {dur}分" if dur else f"✅ {detail or ''}".strip()
    if status == "leave":
        return f"📝 {detail or '請假'}".strip()
    return "—"


def build_coach_attendance_matrix(year: int, month: int) -> pd.DataFrame:
    import calendar

    from utils.helpers import format_train_duration

    students = get_students()
    att = get_attendance_for_month(year, month)
    days_in_month = calendar.monthrange(year, month)[1]
    rows: list[dict] = []

    for student in students:
        name = safe_str(student.get("name"))
        row: dict = {"姓名": name, "專項": safe_str(student.get("specialty"))}
        present = leave = 0
        total_min = 0

        sub = att[att["athlete_name"].astype(str) == name] if not att.empty else pd.DataFrame()
        by_date: dict[str, dict] = {}
        for _, rec in sub.iterrows():
            ds = normalize_date_str(rec.get("date"))
            if ds:
                by_date[ds] = rec.to_dict()

        for day in range(1, days_in_month + 1):
            ds = f"{year}-{month:02d}-{day:02d}"
            if ds in by_date:
                rec = by_date[ds]
                status = safe_str(rec.get("status"))
                detail = safe_str(rec.get("detail"))
                dur = safe_int(rec.get("duration_minutes"), 0)
                row[str(day)] = _attendance_cell(status, detail, dur)
                if status == "present":
                    present += 1
                    total_min += dur
                elif status == "leave":
                    leave += 1
            else:
                row[str(day)] = "—"

        row["出席"] = present
        row["請假"] = leave
        row["訓練時數"] = format_train_duration(total_min)
        total_marked = present + leave
        row["出席率"] = f"{round(present / total_marked * 100)}%" if total_marked else "—"
        rows.append(row)

    return pd.DataFrame(rows)


def build_coach_attendance_log(year: int, month: int) -> pd.DataFrame:
    from utils.helpers import format_train_duration

    students = {safe_str(s["name"]): safe_str(s.get("specialty")) for s in get_students()}
    att = get_attendance_for_month(year, month)
    if att.empty:
        return pd.DataFrame(columns=["日期", "姓名", "專項", "狀態", "詳情", "訓練時數"])

    rows = []
    status_labels = {"present": "出席", "leave": "請假"}
    for _, rec in att.sort_values(["date", "athlete_name"]).iterrows():
        name = safe_str(rec.get("athlete_name"))
        status = safe_str(rec.get("status"))
        dur = safe_int(rec.get("duration_minutes"), 0)
        rows.append({
            "日期": normalize_date_str(rec.get("date")),
            "姓名": name,
            "專項": students.get(name, ""),
            "狀態": status_labels.get(status, status),
            "詳情": safe_str(rec.get("detail")),
            "訓練時數": format_train_duration(dur) if status == "present" else "—",
        })
    return pd.DataFrame(rows)


# ── Injuries ────────────────────────────────────────────────────────────────

def load_injuries() -> pd.DataFrame:
    return _read(INJURIES_FILE, INJURY_COLUMNS)


def save_injuries(df: pd.DataFrame) -> None:
    _write(INJURIES_FILE, df, INJURY_COLUMNS)


def add_injury(data: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_injuries()
    data["id"] = _next_id(df)
    save_injuries(pd.concat([df, pd.DataFrame([data])], ignore_index=True))


# ── Competitions ────────────────────────────────────────────────────────────

def load_competitions() -> pd.DataFrame:
    return _read(COMPETITIONS_FILE, COMP_COLUMNS)


def save_competitions(df: pd.DataFrame) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    _write(COMPETITIONS_FILE, df, COMP_COLUMNS)


def add_competition(data: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_competitions()
    data["id"] = _uid()
    data["registered"] = data.get("registered", "")
    data["published"] = data.get("published", "1")
    data.setdefault("link", "")
    for col in ("deadline", "assembly_time", "transport", "notes"):
        data.setdefault(col, "")
    save_competitions(pd.concat([df, pd.DataFrame([data])], ignore_index=True))


def update_competition(comp_id: str, data: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_competitions()
    idx = df.index[df["id"].astype(str) == comp_id]
    if idx.empty:
        return
    for key, value in data.items():
        if key in COMP_COLUMNS and key != "id":
            df.loc[idx[0], key] = value
    save_competitions(df)


def delete_competition(comp_id: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_competitions()
    save_competitions(df[df["id"].astype(str) != comp_id])
    delete_comp_entries_for_comp(comp_id)


def parse_comp_events(value) -> list[str]:
    if is_missing(value):
        return []
    events = []
    for part in str(value).split(","):
        name = safe_str(part)
        if name and name.lower() not in ("nan", "none"):
            events.append(name)
    return events


def _is_comp_published(value) -> bool:
    text = safe_str(value).lower()
    if not text or text in ("nan", "none"):
        return True
    if text in ("0", "false", "no", "n", "否"):
        return False
    return text in ("1", "true", "yes", "y", "是")


def competition_to_dict(row) -> dict:
    data = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    comp_id = safe_str(data.get("id"))
    return {
        "id": comp_id,
        "name": safe_str(data.get("name")),
        "date": normalize_date_str(data.get("date")),
        "events": parse_comp_events(data.get("event")),
        "location": safe_str(data.get("location")),
        "link": safe_str(data.get("link")),
        "deadline": normalize_date_str(data.get("deadline")) if safe_str(data.get("deadline")) else "",
        "notes": safe_str(data.get("notes")),
        "published": _is_comp_published(data.get("published")),
        "registration_count": count_comp_registrations(comp_id),
    }


def load_comp_entries() -> pd.DataFrame:
    return _read(COMP_ENTRIES_FILE, COMP_ENTRY_COLUMNS)


def save_comp_entries(df: pd.DataFrame) -> None:
    _write(COMP_ENTRIES_FILE, df, COMP_ENTRY_COLUMNS)


def get_comp_entry(comp_id: str, athlete_name: str) -> dict | None:
    df = load_comp_entries()
    if df.empty:
        return None
    match = df[
        (df["comp_id"].astype(str) == comp_id)
        & (df["athlete_name"].astype(str) == athlete_name)
    ]
    if match.empty:
        return None
    row = match.iloc[-1]
    return {
        "id": safe_str(row["id"]),
        "comp_id": safe_str(row["comp_id"]),
        "athlete_name": safe_str(row["athlete_name"]),
        "username": safe_str(row["username"]),
        "events": parse_comp_events(row.get("events")),
        "event_pbs": parse_entry_pbs(row.get("pbs_json")),
        "submitted_at": safe_str(row["submitted_at"]),
    }


def count_comp_registrations(comp_id: str) -> int:
    df = load_comp_entries()
    if df.empty:
        return 0
    sub = df[df["comp_id"].astype(str) == comp_id]
    return sub["athlete_name"].astype(str).nunique()


def get_comp_entries_for_comp(comp_id: str) -> list[dict]:
    df = load_comp_entries()
    if df.empty:
        return []
    sub = df[df["comp_id"].astype(str) == comp_id]
    return [
        {
            "id": safe_str(row["id"]),
            "comp_id": comp_id,
            "athlete_name": safe_str(row["athlete_name"]),
            "username": safe_str(row["username"]),
            "events": parse_comp_events(row.get("events")),
            "event_pbs": parse_entry_pbs(row.get("pbs_json")),
            "submitted_at": safe_str(row["submitted_at"]),
        }
        for _, row in sub.iterrows()
    ]


def parse_entry_pbs(value) -> dict[str, dict]:
    text = safe_str(value)
    if not text:
        return {}
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict] = {}
    for event, pb in raw.items():
        ev = safe_str(event)
        if not ev or not isinstance(pb, dict):
            continue
        result[ev] = {
            "score": safe_str(pb.get("score")),
            "comp_name": safe_str(pb.get("comp_name")),
            "date": normalize_date_str(pb.get("date")) if safe_str(pb.get("date")) else "",
        }
    return result


def serialize_entry_pbs(event_pbs: dict[str, dict]) -> str:
    clean: dict[str, dict] = {}
    for event, pb in (event_pbs or {}).items():
        ev = safe_str(event)
        if not ev:
            continue
        clean[ev] = {
            "score": safe_str(pb.get("score")),
            "comp_name": safe_str(pb.get("comp_name")),
            "date": normalize_date_str(pb.get("date")) if safe_str(pb.get("date")) else "",
        }
    return json.dumps(clean, ensure_ascii=False)


def resolve_event_pb(athlete_name: str, event: str, manual_pbs: dict[str, dict] | None = None) -> dict:
    auto = get_best_performance_last_year(athlete_name, event)
    if auto.get("score"):
        return {**auto, "source": "record"}
    manual = (manual_pbs or {}).get(event) or {}
    return {
        "score": safe_str(manual.get("score")),
        "comp_name": safe_str(manual.get("comp_name")),
        "date": normalize_date_str(manual.get("date")) if safe_str(manual.get("date")) else "",
        "source": "manual" if manual.get("score") else "",
    }


def submit_comp_entry(
    comp_id: str,
    username: str,
    athlete_name: str,
    events: list[str],
    event_pbs: dict[str, dict] | None = None,
) -> tuple[bool, str]:
    from utils.permissions import PermissionDenied, require_self_username
    try:
        user = require_self_username(username)
        if safe_str(user.get("role")) == "student" and safe_str(user.get("name")) != safe_str(athlete_name):
            return False, "只能提交自己的比賽報名"
    except PermissionDenied as exc:
        return False, exc.message
    if not events:
        return False, "請至少選擇一個比賽項目"
    comp = next((c for c in get_competitions() if c["id"] == comp_id), None)
    if not comp:
        return False, "找不到比賽"
    allowed = set(comp["events"])
    picked = [e for e in events if e in allowed]
    if not picked:
        return False, "所選項目不在此比賽開放項目內"

    stored_pbs: dict[str, dict] = {}
    manual = event_pbs or {}
    for event in picked:
        auto = get_best_performance_last_year(athlete_name, event)
        if auto.get("score"):
            continue
        pb = manual.get(event) or {}
        if not safe_str(pb.get("score")) or not safe_str(pb.get("comp_name")) or not safe_str(pb.get("date")):
            return False, f"請填寫「{event}」的最佳成績、賽事及比賽日期"
        stored_pbs[event] = {
            "score": safe_str(pb.get("score")),
            "comp_name": safe_str(pb.get("comp_name")),
            "date": normalize_date_str(pb.get("date")),
        }

    df = load_comp_entries()
    df = df[~((df["comp_id"].astype(str) == comp_id) & (df["athlete_name"].astype(str) == athlete_name))]
    df = pd.concat([df, pd.DataFrame([{
        "id": _uid(),
        "comp_id": comp_id,
        "athlete_name": athlete_name,
        "username": username,
        "events": ",".join(picked),
        "pbs_json": serialize_entry_pbs(stored_pbs),
        "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
    }])], ignore_index=True)
    save_comp_entries(df)
    return True, ""


def delete_comp_entry(comp_id: str, athlete_name: str) -> None:
    from utils.permissions import require_athlete_self
    require_athlete_self(athlete_name)
    df = load_comp_entries()
    save_comp_entries(df[
        ~((df["comp_id"].astype(str) == comp_id) & (df["athlete_name"].astype(str) == athlete_name))
    ])


def delete_comp_entries_for_comp(comp_id: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_comp_entries()
    save_comp_entries(df[df["comp_id"].astype(str) != comp_id])


def get_best_performance_last_year(athlete_name: str, event: str) -> dict:
    from utils.config import FIELD_EVENTS
    from utils.helpers import parse_field_score, parse_time

    cutoff = (date.today() - timedelta(days=365)).isoformat()
    records: list[dict] = []

    races = load_race_records()
    if not races.empty:
        sub = races[
            (races["athlete_name"].astype(str) == athlete_name)
            & (races["item"].astype(str) == event)
            & (races["date"].astype(str).str[:10] >= cutoff)
        ]
        records.extend(sub.to_dict("records"))

    pending = load_pending_records()
    if not pending.empty:
        sub = pending[
            (pending["athlete_name"].astype(str) == athlete_name)
            & (pending["item"].astype(str) == event)
            & (pending["date"].astype(str).str[:10] >= cutoff)
        ]
        records.extend(sub.to_dict("records"))

    if not records:
        return {"score": "", "comp_name": "", "date": ""}

    if event in FIELD_EVENTS:
        best = max(records, key=lambda r: parse_field_score(r.get("score")))
    else:
        best = min(records, key=lambda r: parse_time(r.get("score")))

    return {
        "score": safe_str(best.get("score")),
        "comp_name": safe_str(best.get("comp_name")),
        "date": normalize_date_str(best.get("date")),
    }


def build_comp_export_df(comp_id: str) -> pd.DataFrame:
    if not next((c for c in get_competitions() if c["id"] == comp_id), None):
        return pd.DataFrame()

    rows: list[dict] = []
    for entry in get_comp_entries_for_comp(comp_id):
        user = get_user_by_name(entry["athlete_name"]) or get_user(entry["username"]) or {}
        for event in entry["events"]:
            pb = resolve_event_pb(entry["athlete_name"], event, entry.get("event_pbs"))
            rows.append({
                "中文名": safe_str(user.get("name")) or entry["athlete_name"],
                "英文名": safe_str(user.get("name_en")),
                "出生年月日": format_birth_display(user),
                "性別": safe_str(user.get("gender")),
                "田總証編號": safe_str(user.get("hkaaa_id")),
                "香港永久性居民": safe_str(user.get("hk_permanent_resident")),
                "參加項目": event,
                "最佳成績": pb.get("score") or "—",
                "賽事": pb.get("comp_name") or "—",
                "比賽日期": pb.get("date") or "—",
            })
    return pd.DataFrame(rows)


def get_competitions(*, published_only: bool = False) -> list[dict]:
    df = load_competitions()
    if df.empty:
        return []
    comps = [competition_to_dict(row) for _, row in df.iterrows()]
    if published_only:
        comps = [c for c in comps if c["published"]]
    comps.sort(key=lambda c: c.get("date") or "")
    return comps


def get_student_competitions(student_name: str) -> list[dict]:
    name = safe_str(student_name)
    result = []
    for comp in get_competitions(published_only=True):
        entry = get_comp_entry(comp["id"], name)
        result.append({
            **comp,
            "is_registered": entry is not None,
            "my_events": entry["events"] if entry else [],
            "my_event_pbs": entry.get("event_pbs", {}) if entry else {},
            "entry_id": entry["id"] if entry else "",
        })
    return result


def set_comp_registration(comp_id: str, athletes: list[str]) -> None:
    df = load_competitions()
    idx = df.index[df["id"].astype(str) == comp_id]
    if idx.empty:
        return
    clean = [a for a in athletes if safe_str(a)]
    df.loc[idx[0], "registered"] = ",".join(clean)
    save_competitions(df)


def toggle_comp_registration(comp_id: str, athlete: str, checked: bool) -> None:
    df = load_competitions()
    idx = df.index[df["id"].astype(str) == comp_id]
    if idx.empty:
        return
    reg = parse_registered(df.loc[idx[0], "registered"])
    if checked and athlete not in reg:
        reg.append(athlete)
    elif not checked:
        reg = [x for x in reg if x != athlete]
    set_comp_registration(comp_id, reg)


def parse_registered(s, valid: list[str] | None = None) -> list[str]:
    from utils.helpers import is_missing, safe_str
    if is_missing(s):
        return []
    reg = []
    for part in str(s).split(","):
        name = safe_str(part)
        if name and name.lower() not in ("nan", "none"):
            reg.append(name)
    if valid is not None:
        allowed = set(valid)
        reg = [name for name in reg if name in allowed]
    return reg


# ── Videos ──────────────────────────────────────────────────────────────────

def load_videos() -> pd.DataFrame:
    return _read(VIDEOS_FILE, VIDEO_COLUMNS)


def save_videos(df: pd.DataFrame) -> None:
    _write(VIDEOS_FILE, df, VIDEO_COLUMNS)


def add_video(data: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_videos()
    data["id"] = _next_id(df)
    data["date"] = data.get("date") or date.today().isoformat()
    save_videos(pd.concat([df, pd.DataFrame([data])], ignore_index=True))


# ── Race records & pending ──────────────────────────────────────────────────

def load_race_records() -> pd.DataFrame:
    return _read(RACE_RECORDS_FILE, RACE_COLUMNS)


def save_race_records(df: pd.DataFrame) -> None:
    _write(RACE_RECORDS_FILE, df, RACE_COLUMNS)


def add_race_record(data: dict) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    df = load_race_records()
    wind = float(data.get("wind") or 0)
    data["grade"] = get_grade(data["item"], data["score"], wind)
    data["valid"] = is_wind_valid(data["item"], wind)
    data["id"] = _next_id(df)
    save_race_records(pd.concat([df, pd.DataFrame([data])], ignore_index=True))


def load_pending_records() -> pd.DataFrame:
    return _read(PENDING_FILE, PENDING_COLUMNS)


def save_pending_records(df: pd.DataFrame) -> None:
    _write(PENDING_FILE, df, PENDING_COLUMNS)


def submit_pending_record(data: dict) -> None:
    from utils.permissions import require_athlete_self
    require_athlete_self(safe_str(data.get("athlete_name")))
    df = load_pending_records()
    data["id"] = _uid()
    data["date"] = data.get("date") or date.today().isoformat()
    save_pending_records(pd.concat([df, pd.DataFrame([data])], ignore_index=True))


def approve_pending_record(record_id: str) -> None:
    from utils.permissions import enforce_coach_if_logged_in
    enforce_coach_if_logged_in()
    pending = load_pending_records()
    match = pending[pending["id"].astype(str) == record_id]
    if match.empty:
        return
    row = match.iloc[0].to_dict()
    add_race_record(row)
    save_pending_records(pending[pending["id"].astype(str) != record_id])


def get_pb_by_event() -> dict:
    records = load_race_records()
    if records.empty:
        return {}
    valid = records[records["valid"].astype(str).isin(["True", "true", "1", True])]
    best = {}
    from utils.helpers import parse_time
    for _, r in valid.iterrows():
        item = r["item"]
        if item not in best or parse_time(r["score"]) < parse_time(best[item]["score"]):
            best[item] = r.to_dict()
    return best


def get_student_gender_map() -> dict[str, str]:
    users = load_users()
    if users.empty:
        return {}
    students = users[users["role"].astype(str) == "student"]
    return {
        safe_str(row["name"]): safe_str(row.get("gender"))
        for _, row in students.iterrows()
        if safe_str(row.get("name"))
    }


def _valid_race_records() -> pd.DataFrame:
    records = load_race_records()
    if records.empty:
        return records
    return records[records["valid"].astype(str).str.lower().isin(["true", "1"])]


def _score_value(item: str, score: str) -> float:
    from utils.config import FIELD_EVENTS
    from utils.helpers import parse_field_score, parse_time

    if item in FIELD_EVENTS:
        return parse_field_score(score)
    return parse_time(score)


def _is_better_score(item: str, score: str, than_score: str) -> bool:
    from utils.config import FIELD_EVENTS

    a = _score_value(item, score)
    b = _score_value(item, than_score)
    if item in FIELD_EVENTS:
        return a > b
    return a < b


def _rank_sort_key(item: str, score: str) -> float:
    from utils.config import FIELD_EVENTS

    val = _score_value(item, score)
    if item in FIELD_EVENTS:
        return -val
    return val


def _format_improvement(item: str, delta: float) -> str:
    from utils.config import FIELD_EVENTS

    if delta <= 0:
        return "—"
    if item in FIELD_EVENTS:
        return f"+{delta:.2f}"
    return f"↑ {delta:.2f} 秒"


def get_pb_leaderboard_by_gender(event: str, gender: str) -> list[dict]:
    """Rank students by best valid score within gender + event; include improvement."""
    from utils.config import FIELD_EVENTS

    valid = _valid_race_records()
    if valid.empty:
        return []

    gender_map = get_student_gender_map()
    sub = valid[valid["item"].astype(str) == event]
    by_athlete: dict[str, list[dict]] = {}
    for _, row in sub.iterrows():
        name = safe_str(row["athlete_name"])
        if gender_map.get(name) != gender:
            continue
        by_athlete.setdefault(name, []).append(row.to_dict())

    rows: list[dict] = []
    for name, recs in by_athlete.items():
        recs.sort(key=lambda r: normalize_date_str(r.get("date")))
        best = recs[0]
        for rec in recs[1:]:
            if _is_better_score(event, rec["score"], best["score"]):
                best = rec
        first = recs[0]
        first_val = _score_value(event, first["score"])
        best_val = _score_value(event, best["score"])
        if event in FIELD_EVENTS:
            improvement = best_val - first_val
        else:
            improvement = first_val - best_val

        rows.append({
            "athlete_name": name,
            "best_score": safe_str(best["score"]),
            "best_date": normalize_date_str(best.get("date")),
            "comp_name": safe_str(best.get("comp_name")),
            "grade": safe_str(best.get("grade")),
            "first_score": safe_str(first["score"]),
            "first_date": normalize_date_str(first.get("date")),
            "improvement": improvement,
            "improvement_text": _format_improvement(event, improvement) if len(recs) >= 2 else "—",
            "records_count": len(recs),
            "_sort": _rank_sort_key(event, best["score"]),
        })

    rows.sort(key=lambda r: r["_sort"])
    for i, row in enumerate(rows, 1):
        row["rank"] = i
        row.pop("_sort", None)
    return rows


# ── Seed ────────────────────────────────────────────────────────────────────


def clear_test_data(*, clear_programs: bool = True) -> dict[str, int]:
    """Remove demo accounts, their records, and seeded calendar programs."""
    from utils.production import enable_production_mode

    stats = purge_test_student_records(clear_programs=clear_programs)
    users = load_users()
    stats["users_removed"] = int(users["username"].astype(str).isin(TEST_USERNAMES).sum())
    users = users[~users["username"].astype(str).isin(TEST_USERNAMES)]
    users = users.drop_duplicates(subset=["username"], keep="first").reset_index(drop=True)
    save_users(users)

    pending_sp = load_pending_specialty()
    if not pending_sp.empty and "username" in pending_sp.columns:
        pending_sp = pending_sp[~pending_sp["username"].astype(str).isin(TEST_USERNAMES)]
        save_pending_specialty(pending_sp.reset_index(drop=True))

    enable_production_mode()
    return stats


def purge_test_student_records(*, clear_programs: bool = False) -> dict[str, int]:
    """Remove demo student records (陳大文、林明美等) from logs and related tables."""
    stats: dict[str, int] = {}

    def _drop_names(df: pd.DataFrame, col: str) -> pd.DataFrame:
        if df.empty or col not in df.columns:
            return df
        return df[~df[col].astype(str).isin(TEST_STUDENT_NAMES)].reset_index(drop=True)

    old_logs = load_logs()
    logs = _drop_names(old_logs, "student_name")
    stats["logs_removed"] = len(old_logs) - len(logs)
    save_logs(logs)

    att = _drop_names(load_attendance(), "athlete_name")
    save_attendance(att)

    wellness = _drop_names(load_wellness(), "athlete_name")
    save_wellness(wellness)

    injuries = _drop_names(load_injuries(), "athlete_name")
    save_injuries(injuries)

    videos = _drop_names(load_videos(), "athlete_name")
    save_videos(videos)

    pending = _drop_names(load_pending_records(), "athlete_name")
    save_pending_records(pending)

    race = _drop_names(load_race_records(), "athlete_name")
    save_race_records(race)

    entries = _drop_names(load_comp_entries(), "athlete_name")
    save_comp_entries(entries)

    if clear_programs:
        progs = load_programs()
        stats["programs_cleared"] = len(progs)
        save_programs(pd.DataFrame(columns=PROGRAM_COLUMNS))
    else:
        stats["programs_cleared"] = 0

    return stats


def _seed_programs() -> None:
    existing = load_programs()
    if len(existing) >= 14:
        return
    today = date.today()
    types = ["間歇跑", "節奏跑", "恢復跑", "技術課", "肌力課", "休息"]
    existing_dates = set(existing["date"].astype(str).tolist()) if not existing.empty else set()
    rows = []
    for i in range(-7, 15):
        dt = today + timedelta(days=i)
        ds = dt.isoformat()
        if ds in existing_dates:
            continue
        tp = types[(i + 7) % len(types)]
        w = TRAIN_TYPES[tp]["weight"]
        rows.append({
            "date": ds,
            "title": "休息日" if tp == "休息" else f"{tp}訓練",
            "type": tp, "group": "全體組員",
            "sets": 5 if tp == "間歇跑" else 0, "reps": 3 if tp == "間歇跑" else 0,
            "dist": 200 if tp == "間歇跑" else 0,
            "rest": "", "duration": 0 if tp == "休息" else (45 if tp == "肌力課" else 60),
            "rpe": 4 if tp == "恢復跑" else 7, "tips": "依教練指示完成",
            "phase": "", "week_theme": "", "target_seconds": 65.0 if tp == "間歇跑" else 0,
            "load": int((0 if tp == "休息" else 60) * 7 * w),
            "exercises": "", "tech_focus": "", "field_event": "跳遠", "attempts": 10,
            "start_time": "", "end_time": "", "venue": "", "venue_other": "",
        })
    if rows:
        save_programs(pd.concat([existing, pd.DataFrame(rows)], ignore_index=True))


def ensure_coach_exists() -> None:
    """Ensure at least one coach account exists (production-safe)."""
    from utils.cloud_deploy import default_coach_credentials
    from utils.passwords import hash_password

    users = load_users()
    if not users.empty and (users["role"].astype(str) == "coach").any():
        return
    coach_user, coach_pass = default_coach_credentials()
    coach_row = {col: None for col in USER_COLUMNS}
    coach_row.update({
        "username": coach_user,
        "name": "關添樂",
        "role": "coach",
        "password": hash_password(coach_pass),
        "specialty": "",
        "phone": "",
        "child_name": "",
        "school": "",
        "emergency_contact": "",
        "emergency_phone": "",
        "health": "",
        "gender": "",
        "name_en": "",
        "birth_year": "",
        "birth_date": "",
        "hkaaa_id": "",
        "hk_permanent_resident": "",
        "avatar": "",
    })
    if users.empty:
        save_users(pd.DataFrame([coach_row]))
    else:
        save_users(pd.concat([users, pd.DataFrame([coach_row])], ignore_index=True))


def init_sample_data() -> None:
    from utils.production import is_production
    from utils.supabase_config import is_supabase_enabled

    if is_production() or is_supabase_enabled():
        ensure_coach_exists()
        if _read(PERIOD_FILE, PERIOD_COLUMNS).empty:
            save_periodization(DEFAULT_PERIODIZATION)
        return

    _seed_programs()
    if _read(PERIOD_FILE, PERIOD_COLUMNS).empty:
        save_periodization(DEFAULT_PERIODIZATION)

    if load_users().empty:
        from utils.passwords import hash_password

        seed_users = [
            {"username": "ktll", "name": "關添樂", "role": "coach", "password": "170330",
             "specialty": "", "phone": "", "child_name": "", "school": "", "gender": "",
             "emergency_contact": "", "emergency_phone": "", "health": ""},
            {"username": "student1", "name": "陳大文", "role": "student", "password": "123",
             "specialty": "短跑", "phone": "0912-345-678", "school": "開明中學", "gender": "男",
             "emergency_contact": "王大明", "emergency_phone": "0922-333-444", "health": "無", "child_name": ""},
            {"username": "student2", "name": "林明美", "role": "student", "password": "123",
             "specialty": "中長跑", "phone": "0988-111-222", "school": "開明中學", "gender": "女",
             "emergency_contact": "林媽", "emergency_phone": "0988-333-444", "health": "無", "child_name": ""},
            {"username": "student3", "name": "張豪傑", "role": "student", "password": "123",
             "specialty": "跨欄", "phone": "0977-555-666", "school": "開明中學", "gender": "男",
             "emergency_contact": "張爸", "emergency_phone": "0977-777-888", "health": "無", "child_name": ""},
            {"username": "parent1", "name": "陳家長", "role": "parent", "password": "123",
             "specialty": "", "phone": "0922-111-222", "child_name": "陳大文", "school": "", "gender": "",
             "emergency_contact": "", "emergency_phone": "", "health": ""},
        ]
        for row in seed_users:
            row["password"] = hash_password(str(row["password"]))
        save_users(pd.DataFrame(seed_users))

    logs = load_logs()
    if logs.empty:
        today = date.today().isoformat()
        save_logs(pd.DataFrame([
            {"id": 1, "date": today, "student_name": "陳大文", "event": "400m 間歇訓練",
             "rep_number": 1, "target_seconds": 65.0, "actual_seconds": 66.2, "rpe": 6,
             "injury_notes": "無不適", "duration": 60, "load": 540, "train_type": "間歇跑",
             "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"), "remark": "", "laps_text": "66.2s"},
            {"id": 2, "date": today, "student_name": "陳大文", "event": "400m 間歇訓練",
             "rep_number": 2, "target_seconds": 65.0, "actual_seconds": 65.8, "rpe": 7,
             "injury_notes": "無不適", "duration": 60, "load": 630, "train_type": "間歇跑",
             "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"), "remark": "", "laps_text": "65.8s"},
            {"id": 3, "date": today, "student_name": "林明美", "event": "400m 間歇訓練",
             "rep_number": 1, "target_seconds": 65.0, "actual_seconds": 64.5, "rpe": 5,
             "injury_notes": "左膝", "duration": 60, "load": 450, "train_type": "間歇跑",
             "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"), "remark": "", "laps_text": "64.5s"},
        ]))
        _seed_acwr_history()


def _seed_acwr_history() -> None:
    logs = load_logs()
    if logs.empty or logs["date"].nunique() > 1:
        return
    today = date.today()
    extra, nid = [], _next_id(logs)
    for days_ago in range(1, 14):
        d = (today - timedelta(days=days_ago)).isoformat()
        for name, rpe in [("陳大文", 6 + days_ago % 3), ("林明美", 5 + days_ago % 2), ("張豪傑", 6)]:
            extra.append({"id": nid, "date": d, "student_name": name, "event": "訓練",
                          "rep_number": 1, "target_seconds": 65.0, "actual_seconds": 66.0, "rpe": rpe,
                          "injury_notes": "無不適", "duration": 55, "load": int(55 * rpe * 1.5),
                          "train_type": "間歇跑", "submitted_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                          "remark": "", "laps_text": "66.0s"})
            nid += 1
    save_logs(pd.concat([logs, pd.DataFrame(extra)], ignore_index=True))
