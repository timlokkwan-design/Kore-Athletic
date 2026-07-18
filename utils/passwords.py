"""Password hashing — PBKDF2-SHA256 with legacy plaintext migration."""
from __future__ import annotations

import hashlib
import hmac
import secrets

SCHEME = "pbkdf2_sha256"
ITERATIONS = 260_000
SALT_BYTES = 16


def is_hashed(value: str) -> bool:
    return str(value or "").startswith(f"{SCHEME}$")


def hash_password(password: str, *, min_length: int = 3) -> str:
    plain = str(password or "")
    if len(plain) < min_length:
        raise ValueError("密碼至少需要 3 個字元")
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS,
    ).hex()
    return f"{SCHEME}${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    plain = str(password or "")
    stored = str(stored or "")
    if not stored:
        return False
    if not is_hashed(stored):
        return hmac.compare_digest(plain, stored)
    try:
        scheme, rounds, salt, digest = stored.split("$", 3)
        if scheme != SCHEME:
            return False
        check = hashlib.pbkdf2_hmac(
            "sha256",
            plain.encode("utf-8"),
            salt.encode("utf-8"),
            int(rounds),
        ).hex()
        return hmac.compare_digest(check, digest)
    except (ValueError, TypeError):
        return False
