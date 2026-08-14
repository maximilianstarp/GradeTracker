"""Stateless bearer-token authentication.

Tokens are signed with itsdangerous (already a transitive Flask dependency)
rather than a full JWT library - all we need is "issued for user X, expires
after N days, tamper-proof". Verified against `current_app.config` at call
time (not cached at import time) so each Flask app instance - including a
fresh one per test - uses its own SECRET_KEY.
"""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.models import User, db
from app.utils import error

TOKEN_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days
_SALT = "grade-tracker-auth"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def issue_token(user: User) -> str:
    return _serializer().dumps({"user_id": user.id})


def _extract_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header[len("Bearer ") :].strip() or None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return error("Nicht angemeldet", 401)

        try:
            data = _serializer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
        except SignatureExpired:
            return error("Sitzung abgelaufen, bitte erneut anmelden", 401)
        except BadSignature:
            return error("Ungültiger Token", 401)

        user = db.session.get(User, data.get("user_id"))
        if not user:
            return error("Nutzer nicht gefunden", 401)

        g.current_user = user
        return view(*args, **kwargs)

    return wrapper
