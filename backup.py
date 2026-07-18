"""Zip backup — local data/ or Supabase export."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

from utils.config import DATA_DIR
from utils.site_content import load_site_content


def _backup_from_supabase(buffer: io.BytesIO) -> None:
    from utils import data_store
    from utils.supabase_io import CSV_TO_TABLE, read_csv_table

    column_map = {
        "users.csv": data_store.USER_COLUMNS,
        "programs.csv": data_store.PROGRAM_COLUMNS,
        "training_logs.csv": data_store.LOG_COLUMNS,
        "wellness.csv": data_store.WELLNESS_COLUMNS,
        "periodization.csv": data_store.PERIOD_COLUMNS,
        "attendance.csv": data_store.ATTENDANCE_COLUMNS,
        "injuries.csv": data_store.INJURY_COLUMNS,
        "competitions.csv": data_store.COMP_COLUMNS,
        "comp_entries.csv": data_store.COMP_ENTRY_COLUMNS,
        "videos.csv": data_store.VIDEO_COLUMNS,
        "templates.csv": data_store.TEMPLATE_COLUMNS,
        "pending_records.csv": data_store.PENDING_COLUMNS,
        "pending_specialty.csv": data_store.PENDING_SPECIALTY_COLUMNS,
        "race_records.csv": data_store.RACE_COLUMNS,
    }

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in CSV_TO_TABLE:
            columns = column_map[filename]
            df = read_csv_table(filename, columns)
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            zf.writestr(f"{DATA_DIR}/{filename}", csv_bytes)
        content = load_site_content()
        zf.writestr(
            f"{DATA_DIR}/site_content.json",
            json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8"),
        )


def build_data_backup_zip() -> tuple[bytes, str]:
    from utils.supabase_config import is_supabase_enabled

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"kore-athletic-backup_{stamp}.zip"
    buffer = io.BytesIO()

    if is_supabase_enabled():
        _backup_from_supabase(buffer)
        return buffer.getvalue(), filename

    root = Path(__file__).resolve().parent.parent / DATA_DIR
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if not root.exists():
            return buffer.getvalue(), filename
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.name == ".gitkeep":
                continue
            arcname = Path(DATA_DIR) / path.relative_to(root)
            zf.write(path, arcname.as_posix())
    return buffer.getvalue(), filename
