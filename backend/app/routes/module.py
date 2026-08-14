from flask import Blueprint, g, jsonify, request

from app.auth import login_required
from app.models import GradeAttempt, Modul, Studiengang, SubmissionSeries, db
from app.utils import error, get_owned

bp = Blueprint("module", __name__, url_prefix="/api")


def _resolve_studiengaenge(raw_ids) -> tuple[list[Studiengang] | None, tuple | None]:
    """Returns (studiengaenge, error_response). Empty list is valid = Sonstiges."""
    if raw_ids is None:
        return [], None
    if not isinstance(raw_ids, list):
        return None, error("studiengang_ids muss eine Liste sein")
    try:
        ids = [int(i) for i in raw_ids]
    except (TypeError, ValueError):
        return None, error("studiengang_ids müssen Zahlen sein")

    rows = Studiengang.query.filter(
        Studiengang.id.in_(ids), Studiengang.user_id == g.current_user.id
    ).all()
    if len(rows) != len(set(ids)):
        return None, error("mindestens ein Studiengang wurde nicht gefunden", 404)
    return rows, None


@bp.get("/module")
@login_required
def list_module():
    q = Modul.query.filter_by(user_id=g.current_user.id)
    if "studiengang_id" in request.args:
        raw = request.args["studiengang_id"]
        if raw in ("", "null", "sonstiges"):
            q = q.filter(~Modul.studiengaenge.any())
        else:
            try:
                sid = int(raw)
            except ValueError:
                return error("studiengang_id muss eine Zahl sein")
            q = q.filter(Modul.studiengaenge.any(Studiengang.id == sid))
    rows = q.order_by(Modul.name).all()
    return jsonify([m.to_dict() for m in rows])


@bp.post("/module")
@login_required
def create_modul():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    credits = data.get("credits")

    if not name:
        return error("name ist erforderlich")
    try:
        credits = float(credits)
    except (TypeError, ValueError):
        return error("credits muss eine Zahl sein")
    if credits <= 0:
        return error("credits muss positiv sein")

    studiengaenge, err = _resolve_studiengaenge(data.get("studiengang_ids"))
    if err:
        return err

    modul = Modul(name=name, credits=credits, user_id=g.current_user.id, studiengaenge=studiengaenge)
    db.session.add(modul)
    db.session.commit()
    return jsonify(modul.to_dict()), 201


@bp.get("/module/<int:modul_id>")
@login_required
def get_modul(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Modul nicht gefunden", 404)
    return jsonify(modul.to_dict())


@bp.patch("/module/<int:modul_id>")
@login_required
def update_modul(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Modul nicht gefunden", 404)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return error("name darf nicht leer sein")
        modul.name = name

    if "credits" in data:
        try:
            credits = float(data["credits"])
        except (TypeError, ValueError):
            return error("credits muss eine Zahl sein")
        if credits <= 0:
            return error("credits muss positiv sein")
        modul.credits = credits

    if "studiengang_ids" in data:
        studiengaenge, err = _resolve_studiengaenge(data.get("studiengang_ids"))
        if err:
            return err
        modul.studiengaenge = studiengaenge

    db.session.commit()
    return jsonify(modul.to_dict())


@bp.delete("/module/<int:modul_id>")
@login_required
def delete_modul(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Modul nicht gefunden", 404)
    db.session.delete(modul)
    db.session.commit()
    return "", 204


VALID_KINDS = {"numeric", "pass", "fail"}


@bp.post("/module/<int:modul_id>/grades")
@login_required
def upsert_grade(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Modul nicht gefunden", 404)

    data = request.get_json(silent=True) or {}
    slot = data.get("slot")
    kind = data.get("kind")
    value = data.get("value")

    try:
        slot = int(slot)
    except (TypeError, ValueError):
        return error("slot muss 1, 2 oder 3 sein")
    if slot not in (1, 2, 3):
        return error("slot muss 1, 2 oder 3 sein")
    if kind not in VALID_KINDS:
        return error("kind muss 'numeric', 'pass' oder 'fail' sein")

    if kind == "numeric":
        try:
            value = float(value)
        except (TypeError, ValueError):
            return error("value ist bei kind='numeric' erforderlich")
        if not (1.0 <= value <= 5.0):
            return error("value muss zwischen 1.0 und 5.0 liegen")
    else:
        value = None

    attempt = GradeAttempt.query.filter_by(modul_id=modul_id, slot=slot).first()
    if attempt:
        attempt.kind = kind
        attempt.value = value
    else:
        attempt = GradeAttempt(modul_id=modul_id, slot=slot, kind=kind, value=value)
        db.session.add(attempt)

    db.session.commit()
    return jsonify(modul.to_dict()), 200


@bp.delete("/grades/<int:grade_id>")
@login_required
def delete_grade(grade_id: int):
    attempt = db.session.get(GradeAttempt, grade_id)
    if not attempt or attempt.modul.user_id != g.current_user.id:
        return error("Note nicht gefunden", 404)
    modul_id = attempt.modul_id
    db.session.delete(attempt)
    db.session.commit()
    modul = db.session.get(Modul, modul_id)
    return jsonify(modul.to_dict())


@bp.post("/module/<int:modul_id>/series")
@login_required
def create_series(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Modul nicht gefunden", 404)

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error("name ist erforderlich")

    threshold = data.get("threshold_percent", 50.0)
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        return error("threshold_percent muss eine Zahl sein")
    if not (0 <= threshold <= 100):
        return error("threshold_percent muss zwischen 0 und 100 liegen")

    total_weeks = data.get("total_weeks")
    if total_weeks is not None:
        try:
            total_weeks = int(total_weeks)
        except (TypeError, ValueError):
            return error("total_weeks muss eine ganze Zahl sein")

    series = SubmissionSeries(
        modul_id=modul_id, name=name, threshold_percent=threshold, total_weeks=total_weeks
    )
    db.session.add(series)
    db.session.commit()
    return jsonify(modul.to_dict()), 201
