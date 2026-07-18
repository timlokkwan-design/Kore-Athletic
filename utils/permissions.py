"""Server-side role checks — enforce on every sensitive action."""
from __future__ import annotations

from utils.helpers import safe_str


class PermissionDenied(Exception):
    def __init__(self, message: str = "沒有權限執行此操作"):
        self.message = message
        super().__init__(message)


def get_session_user() -> dict | None:
    try:
        import streamlit as st
    except ImportError:
        return None
    user = st.session_state.get("user")
    if not user or not isinstance(user, dict):
        return None
    return user


def _role(user: dict) -> str:
    return safe_str(user.get("role"))


def check_role(*roles: str) -> dict:
    user = get_session_user()
    if not user:
        raise PermissionDenied("請先登入")
    role = _role(user)
    if role == "pending":
        raise PermissionDenied("帳號待教練審批中")
    if role == "removed":
        raise PermissionDenied("此帳號已移出隊伍")
    if role not in roles:
        raise PermissionDenied("沒有權限執行此操作")
    return user


def require_login() -> dict:
    user = get_session_user()
    if not user:
        raise PermissionDenied("請先登入")
    role = _role(user)
    if role == "pending":
        raise PermissionDenied("帳號待教練審批中")
    if role == "removed":
        raise PermissionDenied("此帳號已移出隊伍")
    return user


def require_coach() -> dict:
    return check_role("coach")


def require_student() -> dict:
    return check_role("student")


def require_parent() -> dict:
    return check_role("parent")


def require_self_username(username: str) -> dict:
    user = require_login()
    if _role(user) == "coach":
        return user
    if safe_str(user.get("username")) != safe_str(username):
        raise PermissionDenied("只能操作自己的帳號")
    return user


def require_athlete_self(athlete_name: str) -> dict:
    user = require_login()
    if _role(user) == "coach":
        return user
    if _role(user) == "student" and safe_str(user.get("name")) == safe_str(athlete_name):
        return user
    raise PermissionDenied("只能操作自己的紀錄")


def enforce_coach_if_logged_in() -> None:
    if get_session_user() is not None:
        require_coach()


def enforce_self_username_if_logged_in(username: str) -> None:
    if get_session_user() is not None:
        require_self_username(username)


def enforce_athlete_self_if_logged_in(athlete_name: str) -> None:
    if get_session_user() is not None:
        require_athlete_self(athlete_name)
