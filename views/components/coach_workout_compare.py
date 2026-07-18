"""Coach — recent same-group workout history for side-by-side comparison."""

from __future__ import annotations

from datetime import date

import streamlit as st

from utils.config import GROUP_OPTIONS, WEEKDAY_SHORT, group_display_label, normalize_group, normalize_train_type
from utils.data_store import get_group_training_history
from utils.helpers import format_meters_short, safe_str, workout_detail, workout_volume_from_program

_COMPARE_GROUPS = [g for g in GROUP_OPTIONS if g != "全體組員"]


def _history_card(prog: dict, *, highlight: bool = False) -> str:
    ds = safe_str(prog.get("date"))
    try:
        d = date.fromisoformat(ds)
        date_label = f"{d.month}/{d.day}（{WEEKDAY_SHORT[d.weekday()]}）"
    except ValueError:
        date_label = ds
    tp = normalize_train_type(safe_str(prog.get("type")))
    detail = workout_detail(prog)
    preview = detail.split("\n")[0].strip() if detail else (tp if tp != "訓練" else "—")
    if len(preview) > 42:
        preview = preview[:41] + "…"
    vol = format_meters_short(workout_volume_from_program(prog)["total_meters"])
    vol_line = f"<div style='color:#1d4ed8;font-weight:700;font-size:12px;margin-top:4px;'>{vol}</div>" if vol else ""
    border = "2px solid #1d4ed8" if highlight else "1px solid #cbd5e1"
    bg = "#eff6ff" if highlight else "#f8fafc"
    type_badge = f"<span style='font-size:10px;color:#64748b;'> · {tp}</span>" if tp in ("比賽",) else ""
    return (
        f"<div style='background:{bg};border:{border};border-radius:8px;"
        f"padding:8px 10px;margin-bottom:6px;min-height:4.5rem;'>"
        f"<div style='font-size:12px;font-weight:700;color:#1e3a8a;'>{date_label}{type_badge}</div>"
        f"<div style='font-size:11px;color:#475569;margin-top:4px;line-height:1.35;'>{preview or '—'}</div>"
        f"{vol_line}</div>"
    )


def _render_group_column(
    selected: date,
    group: str,
    *,
    highlight: bool,
    days_back: int = 14,
) -> None:
    label = group_display_label(group)
    history = get_group_training_history(selected, group, days_back=days_back)
    if highlight:
        st.markdown(f"**🔹 {label}**")
    else:
        st.markdown(f"**{label}**")
    if not history:
        st.caption("近2週無訓練紀錄")
        return
    html = "".join(_history_card(p, highlight=highlight) for p in history)
    st.markdown(html, unsafe_allow_html=True)


def render_workout_history_compare(
    selected: date,
    *,
    highlight_group: str | None = None,
    groups: list[str] | None = None,
    days_back: int = 14,
) -> None:
    """
    Show past training plans by group in columns (短跑 / 中長跑 / 跨欄).
    highlight_group: currently edited group (blue border on column title context).
    """
    show_groups = groups or _COMPARE_GROUPS
    if highlight_group:
        hg = normalize_group(highlight_group)
        ordered = [hg] + [g for g in show_groups if normalize_group(g) != hg]
        show_groups = ordered

    st.markdown("#### 📊 近2週同組別跑案參考")
    st.caption(
        f"選定日 **{selected.month}/{selected.day}** · "
        f"各組別獨立顯示（短跑對短跑、中長跑對中長跑）· 方便與下方跑案比較"
    )

    n = len(show_groups)
    cols = st.columns(n)
    for col, grp in zip(cols, show_groups):
        with col:
            _render_group_column(
                selected,
                grp,
                highlight=highlight_group is not None and normalize_group(grp) == normalize_group(highlight_group),
                days_back=days_back,
            )
