from flask import Blueprint, jsonify, request

from app.models import Studiengang, db
from app.utils import error

bp = Blueprint("studiengaenge", __name__, url_prefix="/api/studiengaenge")


@bp.get("")
def list_studiengaenge():
    rows = Studiengang.query.order_by(Studiengang.name).all()
    return jsonify([s.to_dict() for s in rows])


@bp.post("")
def create_studiengang():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error("name ist erforderlich")
    if name.lower() == "sonstiges":
        return error("'Sonstiges' ist reserviert und kein eigener Studiengang")
    if Studiengang.query.filter(db.func.lower(Studiengang.name) == name.lower()).first():
        return error("Studiengang existiert bereits", 409)

    sg = Studiengang(name=name)
    db.session.add(sg)
    db.session.commit()
    return jsonify(sg.to_dict()), 201


@bp.get("/<int:studiengang_id>")
def get_studiengang(studiengang_id: int):
    sg = db.session.get(Studiengang, studiengang_id)
    if not sg:
        return error("Studiengang nicht gefunden", 404)
    return jsonify(sg.to_dict())


@bp.patch("/<int:studiengang_id>")
def update_studiengang(studiengang_id: int):
    sg = db.session.get(Studiengang, studiengang_id)
    if not sg:
        return error("Studiengang nicht gefunden", 404)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return error("name darf nicht leer sein")
        sg.name = name
    db.session.commit()
    return jsonify(sg.to_dict())


@bp.delete("/<int:studiengang_id>")
def delete_studiengang(studiengang_id: int):
    sg = db.session.get(Studiengang, studiengang_id)
    if not sg:
        return error("Studiengang nicht gefunden", 404)
    db.session.delete(sg)
    db.session.commit()
    return "", 204
