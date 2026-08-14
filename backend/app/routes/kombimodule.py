from flask import Blueprint, g, jsonify, request

from app.auth import login_required
from app.models import KombiModul, Modul, Studiengang, db
from app.utils import error, get_owned

bp = Blueprint("kombimodule", __name__, url_prefix="/api/kombimodule")


def _resolve_source_modules(raw_ids):
    if not isinstance(raw_ids, list) or len(raw_ids) < 2:
        return None, error("source_module_ids must be a list with at least 2 module IDs")
    try:
        ids = [int(i) for i in raw_ids]
    except (TypeError, ValueError):
        return None, error("source_module_ids must be numbers")
    if len(set(ids)) != len(ids):
        return None, error("source_module_ids must not repeat")

    modules = Modul.query.filter(Modul.id.in_(ids), Modul.user_id == g.current_user.id).all()
    if len(modules) != len(ids):
        return None, error("at least one source module was not found", 404)
    return modules, None


@bp.get("")
@login_required
def list_kombimodule():
    q = KombiModul.query.filter_by(user_id=g.current_user.id)
    if "studiengang_id" in request.args:
        try:
            q = q.filter(KombiModul.studiengang_id == int(request.args["studiengang_id"]))
        except ValueError:
            return error("studiengang_id must be a number")
    rows = q.order_by(KombiModul.name).all()
    return jsonify([k.to_dict() for k in rows])


@bp.post("")
@login_required
def create_kombimodul():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    credits = data.get("credits")
    studiengang_id = data.get("studiengang_id")

    if not name:
        return error("name is required")
    try:
        credits = float(credits)
    except (TypeError, ValueError):
        return error("credits must be a number")
    if credits <= 0:
        return error("credits must be positive")

    try:
        studiengang_id = int(studiengang_id)
    except (TypeError, ValueError):
        return error("studiengang_id is required (combined modules need a program)")
    if not get_owned(Studiengang, studiengang_id, g.current_user.id):
        return error("Program not found", 404)

    modules, err = _resolve_source_modules(data.get("source_module_ids"))
    if err:
        return err

    kombi = KombiModul(
        name=name,
        credits=credits,
        studiengang_id=studiengang_id,
        user_id=g.current_user.id,
        source_module=modules,
    )
    db.session.add(kombi)
    db.session.commit()
    return jsonify(kombi.to_dict()), 201


@bp.get("/<int:kombi_id>")
@login_required
def get_kombimodul(kombi_id: int):
    kombi = get_owned(KombiModul, kombi_id, g.current_user.id)
    if not kombi:
        return error("Combined module not found", 404)
    return jsonify(kombi.to_dict())


@bp.patch("/<int:kombi_id>")
@login_required
def update_kombimodul(kombi_id: int):
    kombi = get_owned(KombiModul, kombi_id, g.current_user.id)
    if not kombi:
        return error("Combined module not found", 404)

    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return error("name must not be empty")
        kombi.name = name
    if "credits" in data:
        try:
            credits = float(data["credits"])
        except (TypeError, ValueError):
            return error("credits must be a number")
        if credits <= 0:
            return error("credits must be positive")
        kombi.credits = credits
    if "studiengang_id" in data:
        try:
            sid = int(data["studiengang_id"])
        except (TypeError, ValueError):
            return error("studiengang_id must be a number")
        if not get_owned(Studiengang, sid, g.current_user.id):
            return error("Program not found", 404)
        kombi.studiengang_id = sid
    if "source_module_ids" in data:
        modules, err = _resolve_source_modules(data.get("source_module_ids"))
        if err:
            return err
        kombi.source_module = modules

    db.session.commit()
    return jsonify(kombi.to_dict())


@bp.delete("/<int:kombi_id>")
@login_required
def delete_kombimodul(kombi_id: int):
    kombi = get_owned(KombiModul, kombi_id, g.current_user.id)
    if not kombi:
        return error("Combined module not found", 404)
    db.session.delete(kombi)
    db.session.commit()
    return "", 204
