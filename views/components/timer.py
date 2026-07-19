"""Client-side lap timer — smooth display without full-page rerun."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

_TIMER_HTML = """
<div id="wrap" style="font-family:system-ui,sans-serif;">
  <div id="display" style="text-align:center;font-size:2.4rem;font-family:monospace;
    color:#10b981;background:#0f172a;padding:1rem;border-radius:10px;margin-bottom:0.75rem;">
    00:00.00
  </div>
  <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem;">
    <button id="toggle" style="flex:1;padding:0.85rem;font-weight:700;border:none;border-radius:8px;
      background:#2563eb;color:#fff;font-size:1rem;">開始</button>
    <button id="lap" style="flex:1;padding:0.85rem;font-weight:700;border:none;border-radius:8px;
      background:#059669;color:#fff;font-size:1rem;">記圈</button>
    <button id="reset" style="flex:1;padding:0.85rem;font-weight:700;border:none;border-radius:8px;
      background:#64748b;color:#fff;font-size:1rem;">重置</button>
  </div>
  <div id="laps" style="font-size:0.9rem;color:#334155;max-height:140px;overflow-y:auto;"></div>
</div>
<script>
(function(){
  let running = false, startTs = 0, elapsed = 0, lastLap = 0, laps = [], raf = 0;
  const display = document.getElementById('display');
  const lapsEl = document.getElementById('laps');
  const toggle = document.getElementById('toggle');
  const lapBtn = document.getElementById('lap');
  const resetBtn = document.getElementById('reset');

  function fmt(sec) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return String(m).padStart(2,'0') + ':' + s.toFixed(2).padStart(5,'0');
  }
  function nowElapsed() {
    return running ? elapsed + (performance.now() - startTs) / 1000 : elapsed;
  }
  function tick() {
    display.textContent = fmt(nowElapsed());
    if (running) raf = requestAnimationFrame(tick);
  }
  function renderLaps() {
    if (!laps.length) { lapsEl.innerHTML = ''; return; }
    lapsEl.innerHTML = '<b>分圈紀錄</b><br>' + laps.map((t,i) =>
      'L' + (i+1) + ': <b>' + t.toFixed(2) + 's</b> （累計 ' + fmt(laps.slice(0,i+1).reduce((a,b)=>a+b,0)) + '）'
    ).join('<br>');
  }
  toggle.onclick = function() {
    if (running) {
      elapsed = nowElapsed();
      running = false;
      toggle.textContent = '開始';
      cancelAnimationFrame(raf);
    } else {
      startTs = performance.now();
      running = true;
      toggle.textContent = '暫停';
      tick();
    }
  };
  lapBtn.onclick = function() {
    const cur = nowElapsed();
    if (!running && elapsed === 0) return;
    laps.push(cur - lastLap);
    lastLap = cur;
    renderLaps();
  };
  resetBtn.onclick = function() {
    running = false;
    elapsed = 0; lastLap = 0; laps = [];
    cancelAnimationFrame(raf);
    toggle.textContent = '開始';
    display.textContent = '00:00.00';
    renderLaps();
  };
})();
</script>
"""


def render_lap_timer(on_lap_callback=None) -> list[float]:
    """Render JS stopwatch; returns empty list (laps shown in component)."""
    st.markdown("### ⏱️ 分圈計時器")
    components.html(_TIMER_HTML, height=320, scrolling=False)
    if on_lap_callback:
        st.caption("圈速請對照上方顯示，手動填入訓練數據。")
    return []
