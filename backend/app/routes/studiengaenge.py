from flask import Blueprint, g, jsonify, request

from app.auth import login_required
from app.models import Studiengang, db
from app.utils import error, get_owned

bp = Blueprint("studiengaenge", __name__, url_prefix="/api/studiengaenge")


@bp.get("")
@login_required
def list_studiengaenge():
    rows = Studiengang.query.filter_by(user_id=g.current_user.id).order_by(Studiengang.name).all()
    return jsonify([s.to_dict() for s in rows])


@bp.post("")
@login_required
def create_studiengang():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error("name is required")
    if name.lower() == "sonstiges":
        return error("'Other' is reserved and not a real program")
    exists = Studiengang.query.filter(
        Studiengang.user_id == g.current_user.id, db.func.lower(Studiengang.name) == name.lower()
    ).first()
    if exists:
        return error("Program already exists", 409)

    sg = Studiengang(name=name, user_id=g.current_user.id)
    db.session.add(sg)
    db.session.commit()
    return jsonify(sg.to_dict()), 201


@bp.get("/<int:studiengang_id>")
@login_required
def get_studiengang(studiengang_id: int):
    sg = get_owned(Studiengang, studiengang_id, g.current_user.id)
    if not sg:
        return error("Program not found", 404)
    return jsonify(sg.to_dict())


@bp.patch("/<int:studiengang_id>")
@login_required
def update_studiengang(studiengang_id: int):
    sg = get_owned(Studiengang, studiengang_id, g.current_user.id)
    if not sg:
        return error("Program not found", 404)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return error("name must not be empty")
        sg.name = name
    db.session.commit()
    return jsonify(sg.to_dict())


@bp.delete("/<int:studiengang_id>")
@login_required
def delete_studiengang(studiengang_id: int):
    sg = get_owned(Studiengang, studiengang_id, g.current_user.id)
    if not sg:
        return error("Program not found", 404)
    db.session.delete(sg)
    db.session.commit()
    return "", 204
