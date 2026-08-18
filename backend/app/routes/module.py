from flask import Blueprint, g, jsonify, request

from app.auth import login_required
from app.models import GradeAttempt, Modul, Studiengang, Submission, SubmissionSeries, db
from app.utils import error, get_owned

bp = Blueprint("module", __name__, url_prefix="/api")


def _resolve_studiengaenge(raw_ids) -> tuple[list[Studiengang] | None, tuple | None]:
    """Returns (studiengaenge, error_response). Empty list is valid = Sonstiges."""
    if raw_ids is None:
        return [], None
    if not isinstance(raw_ids, list):
        return None, error("studiengang_ids must be a list")
    try:
        ids = [int(i) for i in raw_ids]
    except (TypeError, ValueError):
        return None, error("studiengang_ids must be numbers")

    rows = Studiengang.query.filter(
        Studiengang.id.in_(ids), Studiengang.user_id == g.current_user.id
    ).all()
    if len(rows) != len(set(ids)):
        return None, error("at least one program was not found", 404)
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
                return error("studiengang_id must be a number")
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
        return error("name is required")
    try:
        credits = float(credits)
    except (TypeError, ValueError):
        return error("credits must be a number")
    if credits <= 0:
        return error("credits must be positive")

    studiengaenge, err = _resolve_studiengaenge(data.get("studiengang_ids"))
    if err:
        return err

    graded = data.get("graded", True)
    if not isinstance(graded, bool):
        return error("graded must be true or false")

    modul = Modul(
        name=name, credits=credits, graded=graded, user_id=g.current_user.id, studiengaenge=studiengaenge
    )
    db.session.add(modul)
    db.session.commit()
    return jsonify(modul.to_dict()), 201


@bp.get("/module/<int:modul_id>")
@login_required
def get_modul(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Module not found", 404)
    return jsonify(modul.to_dict())


@bp.patch("/module/<int:modul_id>")
@login_required
def update_modul(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Module not found", 404)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return error("name must not be empty")
        modul.name = name

    if "credits" in data:
        try:
            credits = float(data["credits"])
        except (TypeError, ValueError):
            return error("credits must be a number")
        if credits <= 0:
            return error("credits must be positive")
        modul.credits = credits

    if "studiengang_ids" in data:
        studiengaenge, err = _resolve_studiengaenge(data.get("studiengang_ids"))
        if err:
            return err
        modul.studiengaenge = studiengaenge

    if "graded" in data:
        graded = data["graded"]
        if not isinstance(graded, bool):
            return error("graded must be true or false")
        if not graded and any(a.kind == "numeric" for a in modul.grade_attempts):
            return error(
                "This module still has a numeric grade attempt - clear it before marking the "
                "module as not graded"
            )
        modul.graded = graded

    db.session.commit()
    return jsonify(modul.to_dict())


@bp.delete("/module/<int:modul_id>")
@login_required
def delete_modul(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Module not found", 404)
    db.session.delete(modul)
    db.session.commit()
    return "", 204


VALID_KINDS = {"numeric", "pass", "fail"}


@bp.post("/module/<int:modul_id>/grades")
@login_required
def upsert_grade(modul_id: int):
    modul = get_owned(Modul, modul_id, g.current_user.id)
    if not modul:
        return error("Module not found", 404)

    data = request.get_json(silent=True) or {}
    slot = data.get("slot")
    kind = data.get("kind")
    value = data.get("value")

    try:
        slot = int(slot)
    except (TypeError, ValueError):
        return error("slot must be 1, 2 or 3")
    if slot not in (1, 2, 3):
        return error("slot must be 1, 2 or 3")
    if kind not in VALID_KINDS:
        return error("kind must be 'numeric', 'pass' or 'fail'")
    if kind == "numeric" and not modul.graded:
        return error("This module is not graded - only 'passed' or 'failed' attempts are allowed")

    if kind == "numeric":
        try:
            value = float(value)
        except (TypeError, ValueError):
            return error("value is required when kind='numeric'")
        if not (1.0 <= value <= 5.0):
            return error("value must be between 1.0 and 5.0")
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
        return error("Grade not found", 404)
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
        return error("Module not found", 404)

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error("name is required")

    threshold = data.get("threshold_percent", 50.0)
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        return error("threshold_percent must be a number")
    if not (0 <= threshold <= 100):
        return error("threshold_percent must be between 0 and 100")

    total_weeks = data.get("total_weeks")
    points_per_week = None
    if total_weeks is not None:
        try:
            total_weeks = int(total_weeks)
        except (TypeError, ValueError):
            return error("total_weeks must be a whole number")
        if total_weeks <= 0:
            return error("total_weeks must be positive")
        try:
            points_per_week = float(data.get("points_per_week"))
        except (TypeError, ValueError):
            return error("points_per_week is required (and must be a number) when total_weeks is set")
        if points_per_week <= 0:
            return error("points_per_week must be positive")

    series = SubmissionSeries(
        modul_id=modul_id, name=name, threshold_percent=threshold, total_weeks=total_weeks
    )
    db.session.add(series)
    db.session.flush()  # assigns series.id, needed for the Submission rows below

    if total_weeks is not None:
        # Pre-fill every week at 0 achieved so progress/Zulassung can be
        # estimated immediately, before any assignment has actually been
        # done - weeks can still be added/removed individually later if the
        # real count changes.
        for week in range(1, total_weeks + 1):
            db.session.add(
                Submission(
                    series_id=series.id, week_number=week, points_achieved=0, points_max=points_per_week
                )
            )

    db.session.commit()
    return jsonify(modul.to_dict()), 201
