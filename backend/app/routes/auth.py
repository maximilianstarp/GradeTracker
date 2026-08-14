from flask import Blueprint, g, jsonify, request

from app.auth import issue_token, login_required
from app.models import User, db
from app.utils import error

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

MIN_PASSWORD_LENGTH = 8


def _normalize_email(raw: str) -> str:
    return (raw or "").strip().lower()


def _is_valid_email(email: str) -> bool:
    if "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and not domain.startswith(".") and not domain.endswith(".")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not name:
        return error("Name ist erforderlich")
    if not _is_valid_email(email):
        return error("Bitte eine gültige E-Mail-Adresse angeben")
    if len(password) < MIN_PASSWORD_LENGTH:
        return error(f"Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein")
    if User.query.filter_by(email=email).first():
        return error("E-Mail-Adresse wird bereits verwendet", 409)

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"token": issue_token(user), "user": user.to_dict()}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return error("E-Mail oder Passwort ist falsch", 401)

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
        return error("Aktuelles Passwort ist falsch", 401)

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return error("Name darf nicht leer sein")
        user.name = name

    if "email" in data:
        email = _normalize_email(data.get("email"))
        if not _is_valid_email(email):
            return error("Bitte eine gültige E-Mail-Adresse angeben")
        if email != user.email and User.query.filter_by(email=email).first():
            return error("E-Mail-Adresse wird bereits verwendet", 409)
        user.email = email

    if data.get("new_password"):
        new_password = data["new_password"]
        if len(new_password) < MIN_PASSWORD_LENGTH:
            return error(f"Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein")
        user.set_password(new_password)

    db.session.commit()
    return jsonify(user.to_dict())
