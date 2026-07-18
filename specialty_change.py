"""Student specialty change request UI."""
from __future__ import annotations

import streamlit as st

from utils.config import SPECIALTY_OPTIONS
from utils.data_store import get_pending_specialty_for_user, submit_specialty_change
from utils.helpers import safe_str


def render_specialty_change_request(user: dict) -> None:
    username = safe_str(user.get("username"))
    name = safe_str(user.get("name"))
    current = safe_str(user.get("specialty"))
    pending = get_pending_specialty_for_user(username)

    with st.expander("更改專項（需教練審批）", expanded=bool(pending)):
        st.caption(f"目前專項：**{current or '—'}**")
        if pending:
            reason = pending.get("reason") or "—"
            st.info(
                f"已提交更改申請：**{pending['current_specialty']}** → "
                f"**{pending['requested_specialty']}**（{pending['date']}）\n\n"
                f"原因：{reason}"
            )
            st.caption("待教練審批後才會生效。")
            return

        options = [s for s in SPECIALTY_OPTIONS if s != current] or SPECIALTY_OPTIONS
        new_spec = st.selectbox("申請更改為", options, key="student_specialty_pick")
        reason = st.text_input("原因（選填）", placeholder="例如：近期主攻中長距離", key="student_specialty_reason")
        if st.button("提交專項更改申請", type="primary", key="student_specialty_submit"):
            ok, msg = submit_specialty_change(username, name, current, new_spec, reason)
            if ok:
                st.success("已提交，待教練審批")
                st.rerun()
            st.warning(msg)
