"""V6 lap timer — session-state based."""

import time

import streamlit as st


def _init_timer():
    if "timer" not in st.session_state:
        st.session_state.timer = {
            "running": False, "start": 0.0, "elapsed": 0.0,
            "laps": [], "last_lap": 0.0,
        }


def _elapsed() -> float:
    t = st.session_state.timer
    if t["running"]:
        return t["elapsed"] + (time.time() - t["start"])
    return t["elapsed"]


def _fmt(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"


def render_lap_timer(on_lap_callback=None) -> list[float]:
    """Render stopwatch; return list of lap times in seconds."""
    _init_timer()
    t = st.session_state.timer
    elapsed = _elapsed()

    st.markdown(f"### ⏱️ 分圈計時器")
    st.markdown(
        f"<div style='text-align:center;font-size:2.5rem;font-family:monospace;"
        f"color:#10b981;background:#0f172a;padding:1rem;border-radius:8px;'>{_fmt(elapsed)}</div>",
        unsafe_allow_html=True,
    )

    b1, b2, b3 = st.columns(3)
    if b1.button("開始 / 暫停", use_container_width=True, key="timer_toggle"):
        if t["running"]:
            t["elapsed"] = elapsed
            t["running"] = False
        else:
            t["start"] = time.time()
            t["running"] = True
        st.rerun()
    if b2.button("記圈", use_container_width=True, key="timer_lap", disabled=not t["running"] and elapsed == 0):
        lap_t = elapsed - t["last_lap"]
        t["laps"].append(lap_t)
        t["last_lap"] = elapsed
        if on_lap_callback:
            on_lap_callback(len(t["laps"]), lap_t)
        st.rerun()
    if b3.button("重置", use_container_width=True, key="timer_reset"):
        st.session_state.timer = {"running": False, "start": 0.0, "elapsed": 0.0, "laps": [], "last_lap": 0.0}
        st.rerun()

    if t["laps"]:
        st.markdown("**分圈紀錄**")
        for i, lap in enumerate(t["laps"], 1):
            st.write(f"L{i}: **{lap:.2f}s** （累計 {_fmt(sum(t['laps'][:i]))}）")

    return list(t["laps"])
