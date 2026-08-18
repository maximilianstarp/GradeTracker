import re

from flask import Blueprint, g, jsonify, request

from app.auth import issue_token, login_required
from app.codes import (
    PURPOSE_CHANGE_EMAIL,
    PURPOSE_PASSWORD_RESET,
    PURPOSE_VERIFY_EMAIL,
    check_code,
    clear_code,
    resend_cooldown_remaining,
    set_code,
)
from app.email import send_verification_code
from app.limiter import limiter
from app.models import User, db
from app.utils import error

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

MIN_PASSWORD_LENGTH = 8
USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,30}$")


def _normalize_email(raw: str) -> str:
    return (raw or "").strip().lower()


def _is_valid_email(email: str) -> bool:
    if "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and not domain.startswith(".") and not domain.endswith(".")


def _normalize_username(raw: str) -> str:
    return (raw or "").strip().lower()


def _is_valid_username(username: str) -> bool:
    return bool(USERNAME_RE.match(username))


def _email_taken(email: str, exclude_user_id: int | None = None) -> bool:
    query = User.query.filter_by(email=email)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.first() is not None


@bp.post("/register")
@limiter.limit("5 per hour")
def register():
    data = request.get_json(silent=True) or {}
    username = _normalize_username(data.get("username"))
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not _is_valid_username(username):
        return error("Username must be 3-30 characters: letters, numbers, '.', '_' or '-'")
    if not _is_valid_email(email):
        return error("Please provide a valid email address")
    if len(password) < MIN_PASSWORD_LENGTH:
        return error(f"Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein")
    if User.query.filter_by(username=username).first():
        return error("Username is already taken", 409)
    if _email_taken(email):
        return error("Email address is already in use", 409)

    user = User(username=username, email=email, email_verified=False)
    user.set_password(password)
    code = set_code(user, PURPOSE_VERIFY_EMAIL)
    db.session.add(user)
    db.session.commit()

    send_verification_code(user.email, PURPOSE_VERIFY_EMAIL, code)

    return jsonify({"token": issue_token(user), "user": user.to_dict()}), 201


@bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return error("Email or password is incorrect", 401)

    return jsonify({"token": issue_token(user), "user": user.to_dict()})


@bp.get("/me")
@login_required
def me():
    return jsonify(g.current_user.to_dict())


@bp.patch("/me")
@login_required
def update_me():
    user = g.current_user
    data = request.get_json(silent=True) or {}

    current_password = data.get("current_password") or ""
    if not user.check_password(current_password):
        return error("Current password is incorrect", 401)

    if "username" in data:
        username = _normalize_username(data.get("username"))
        if not _is_valid_username(username):
            return error("Username must be 3-30 characters: letters, numbers, '.', '_' or '-'")
        if username != user.username and User.query.filter(
            User.username == username, User.id != user.id
        ).first():
            return error("Username is already taken", 409)
        user.username = username

    email_changed = False
    if "email" in data:
        email = _normalize_email(data.get("email"))
        if not _is_valid_email(email):
            return error("Please provide a valid email address")
        if email == user.email:
            # Re-submitting the current email cancels any pending change.
            user.pending_email = None
            if user.code_purpose == PURPOSE_CHANGE_EMAIL:
                clear_code(user)
        else:
            if _email_taken(email, exclude_user_id=user.id):
                return error("Email address is already in use", 409)
            code = set_code(user, PURPOSE_CHANGE_EMAIL, pending_email=email)
            email_changed = True

    if data.get("new_password"):
        new_password = data["new_password"]
        if len(new_password) < MIN_PASSWORD_LENGTH:
            return error(f"Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein")
        user.set_password(new_password)

    db.session.commit()

    if email_changed:
        send_verification_code(user.pending_email, PURPOSE_CHANGE_EMAIL, code)

    return jsonify(user.to_dict())


@bp.post("/verify-email")
@login_required
@limiter.limit("20 per hour")
def verify_email():
    user = g.current_user
    if user.email_verified:
        return error("Email is already verified")

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()

    result = check_code(user, PURPOSE_VERIFY_EMAIL, code)
    if not result.ok:
        db.session.commit()  # persist the attempt count bump on wrong codes
        return error(result.error, 400)

    user.email_verified = True
    clear_code(user)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.post("/verify-email-change")
@login_required
@limiter.limit("20 per hour")
def verify_email_change():
    user = g.current_user
    if not user.pending_email:
        return error("No pending email change")

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()

    result = check_code(user, PURPOSE_CHANGE_EMAIL, code)
    if not result.ok:
        db.session.commit()
        return error(result.error, 400)

    if _email_taken(user.pending_email, exclude_user_id=user.id):
        user.pending_email = None
        clear_code(user)
        db.session.commit()
        return error("That email address was taken in the meantime", 409)

    user.email = user.pending_email
    user.pending_email = None
    user.email_verified = True
    clear_code(user)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.post("/resend-code")
@login_required
@limiter.limit("10 per hour")
def resend_code():
    user = g.current_user
    if user.code_purpose not in (PURPOSE_VERIFY_EMAIL, PURPOSE_CHANGE_EMAIL):
        return error("No verification is pending")

    remaining = resend_cooldown_remaining(user)
    if remaining > 0:
        return error(f"Please wait {remaining}s before requesting another code", 429)

    purpose = user.code_purpose
    to_email = user.pending_email if purpose == PURPOSE_CHANGE_EMAIL else user.email
    code = set_code(user, purpose)
    db.session.commit()

    send_verification_code(to_email, purpose, code)
    return jsonify({"message": "Code sent"})


@bp.post("/forgot-password")
@limiter.limit("5 per hour")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = _normalize_email(data.get("email"))
    user = User.query.filter_by(email=email).first() if _is_valid_email(email) else None

    # Same response either way - confirming/denying an email exists would
    # let an attacker enumerate accounts.
    if user and resend_cooldown_remaining(user, PURPOSE_PASSWORD_RESET) == 0:
        code = set_code(user, PURPOSE_PASSWORD_RESET)
        db.session.commit()
        send_verification_code(user.email, PURPOSE_PASSWORD_RESET, code)

    return jsonify({"message": "If that email is registered, a reset code has been sent"})


@bp.post("/reset-password")
@limiter.limit("10 per hour")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = _normalize_email(data.get("email"))
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""

    if len(new_password) < MIN_PASSWORD_LENGTH:
        return error(f"Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein")

    user = User.query.filter_by(email=email).first()
    if not user:
        return error("Invalid or expired code", 400)

    result = check_code(user, PURPOSE_PASSWORD_RESET, code)
    if not result.ok:
        db.session.commit()
        return error(result.error, 400)

    user.set_password(new_password)
    clear_code(user)
    db.session.commit()
    return jsonify({"message": "Password has been reset"})


@bp.delete("/me")
@login_required
def delete_me():
    user = g.current_user
    data = request.get_json(silent=True) or {}

    current_password = data.get("current_password") or ""
    if not user.check_password(current_password):
        return error("Current password is incorrect", 401)

    # User.id is the FK root for Studiengang/Modul/KombiModul (each
    # ondelete="CASCADE"), which in turn cascade down to grade attempts,
    # submission series and submissions - deleting the user is enough.
    db.session.delete(user)
    db.session.commit()

    return "", 204
