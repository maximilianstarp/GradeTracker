"""Short-lived verification codes (email verification, email change,
password reset).

A user has at most one active code at a time, stored right on the User row
- simpler than a separate table, and fine at this app's scale since a new
request always just replaces whatever was pending. The code itself is never
stored in plaintext, only its hash, the same way passwords are handled.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User


def _now() -> datetime:
    # code_expires_at/code_sent_at are plain (timezone-naive) DateTime
    # columns, same as the rest of the schema - stay naive here too so
    # comparisons against values read back from the DB don't blow up.
    return datetime.now(timezone.utc).replace(tzinfo=None)


CODE_LENGTH = 6
CODE_TTL_MINUTES = 15
CODE_MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60

PURPOSE_VERIFY_EMAIL = "verify_email"
PURPOSE_CHANGE_EMAIL = "change_email"
PURPOSE_PASSWORD_RESET = "password_reset"


def generate_code() -> str:
    return f"{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}"


def resend_cooldown_remaining(user: User, purpose: str | None = None) -> int:
    """Seconds left before another code may be requested for this user (0 if
    none). Scoped to `purpose` when given, so e.g. a just-sent email
    verification code doesn't silently swallow an unrelated password-reset
    request made moments later."""
    if not user.code_sent_at:
        return 0
    if purpose is not None and user.code_purpose != purpose:
        return 0
    elapsed = (_now() - user.code_sent_at).total_seconds()
    remaining = RESEND_COOLDOWN_SECONDS - elapsed
    return max(0, int(remaining))


def set_code(user: User, purpose: str, pending_email: str | None = None) -> str:
    """Generates a fresh code for `purpose`, stores its hash on `user`, and
    returns the plaintext code so the caller can email it."""
    code = generate_code()
    user.code_hash = generate_password_hash(code)
    user.code_purpose = purpose
    user.code_expires_at = _now() + timedelta(minutes=CODE_TTL_MINUTES)
    user.code_attempts = 0
    user.code_sent_at = _now()
    if pending_email is not None:
        user.pending_email = pending_email
    return code


def clear_code(user: User) -> None:
    user.code_hash = None
    user.code_purpose = None
    user.code_expires_at = None
    user.code_attempts = 0
    user.code_sent_at = None


@dataclass
class CodeCheck:
    ok: bool
    error: str | None = None


def check_code(user: User, purpose: str, code: str) -> CodeCheck:
    """Verifies `code` against the pending code for `purpose`. Does not clear
    the code on success - callers do that once they've applied its effect."""
    if not user.code_hash or user.code_purpose != purpose:
        return CodeCheck(False, "No verification code is pending")
    if user.code_expires_at is None or user.code_expires_at < _now():
        return CodeCheck(False, "Code has expired, please request a new one")
    if user.code_attempts >= CODE_MAX_ATTEMPTS:
        return CodeCheck(False, "Too many attempts, please request a new code")
    if not check_password_hash(user.code_hash, code):
        user.code_attempts += 1
        return CodeCheck(False, "Invalid code")
    return CodeCheck(True)
