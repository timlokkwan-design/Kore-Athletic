"""WhatsApp deep links — one-tap approval & registration notifications."""
from __future__ import annotations

import re
from urllib.parse import quote

from utils.helpers import safe_str
from utils.site_content import load_site_content


def normalize_whatsapp_number(raw: str) -> str:
    """Strip to digits for wa.me (include country code, no +)."""
    digits = re.sub(r"\D", "", str(raw or ""))
    if not digits:
        return ""
    if digits.startswith("0") and len(digits) == 8:
        return f"852{digits}"
    return digits


def whatsapp_url(phone: str, message: str) -> str:
    """Build wa.me link for any phone number."""
    num = normalize_whatsapp_number(phone)
    if not num:
        return ""
    return f"https://wa.me/{num}?text={quote(message.strip())}"


def coach_whatsapp_url_with_message(message: str) -> str:
    content = load_site_content()
    num = normalize_whatsapp_number(content.get("coach_whatsapp", ""))
    if not num:
        return ""
    if message.strip():
        return f"https://wa.me/{num}?text={quote(message.strip())}"
    return f"https://wa.me/{num}"


def approval_message(*, name: str, username: str) -> str:
    return (
        f"你好 {name}！\n\n"
        f"你的 KORE ATHLETIC 學員帳號已獲教練核准 ✅\n"
        f"登入帳號：{username}\n\n"
        f"請打開訓練系統登入，訓練後記得簽到及填寫日誌。\n"
        f"— KORE ATHLETIC"
    )


def registration_submitted_message(*, name: str, username: str, specialty: str) -> str:
    return (
        f"關教練你好，\n\n"
        f"我已提交 KORE ATHLETIC 註冊申請，請協助審批：\n"
        f"姓名：{name}\n"
        f"帳號：{username}\n"
        f"專項：{specialty}\n\n"
        f"謝謝！"
    )


def build_approval_notify(user: dict) -> dict:
    """After coach approves — link for coach to notify student."""
    name = safe_str(user.get("name"))
    username = safe_str(user.get("username"))
    phone = safe_str(user.get("phone"))
    msg = approval_message(name=name, username=username)
    return {
        "name": name,
        "username": username,
        "url": whatsapp_url(phone, msg),
        "message": msg,
    }


def build_registration_coach_notify(*, name: str, username: str, specialty: str) -> dict:
    """After student registers — link for student to ping coach."""
    msg = registration_submitted_message(name=name, username=username, specialty=specialty)
    return {
        "message": msg,
        "url": coach_whatsapp_url_with_message(msg),
    }
