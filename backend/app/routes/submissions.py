from flask import Blueprint, g, jsonify, request

from app.auth import login_required
from app.models import Submission, SubmissionSeries, db
from app.utils import error

bp = Blueprint("submissions", __name__, url_prefix="/api")


def _get_owned_series(series_id: int) -> SubmissionSeries | None:
    series = db.session.get(SubmissionSeries, series_id)
    if not series or series.modul.user_id != g.current_user.id:
        return None
    return series


def _get_owned_submission(submission_id: int) -> Submission | None:
    submission = db.session.get(Submission, submission_id)
    if not submission or submission.series.modul.user_id != g.current_user.id:
        return None
    return submission


@bp.patch("/series/<int:series_id>")
@login_required
def update_series(series_id: int):
    series = _get_owned_series(series_id)
    if not series:
        return error("Übungsserie nicht gefunden", 404)

    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return error("name darf nicht leer sein")
        series.name = name
    if "threshold_percent" in data:
        try:
            threshold = float(data["threshold_percent"])
        except (TypeError, ValueError):
            return error("threshold_percent muss eine Zahl sein")
        if not (0 <= threshold <= 100):
            return error("threshold_percent muss zwischen 0 und 100 liegen")
        series.threshold_percent = threshold
    if "total_weeks" in data:
        raw = data["total_weeks"]
        if raw is None:
            series.total_weeks = None
        else:
            try:
                series.total_weeks = int(raw)
            except (TypeError, ValueError):
                return error("total_weeks muss eine ganze Zahl sein")

    db.session.commit()
    return jsonify(series.modul.to_dict())


@bp.delete("/series/<int:series_id>")
@login_required
def delete_series(series_id: int):
    series = _get_owned_series(series_id)
    if not series:
        return error("Übungsserie nicht gefunden", 404)
    modul = series.modul
    db.session.delete(series)
    db.session.commit()
    return jsonify(modul.to_dict())


@bp.post("/series/<int:series_id>/submissions")
@login_required
def create_submission(series_id: int):
    series = _get_owned_series(series_id)
    if not series:
        return error("Übungsserie nicht gefunden", 404)

    data = request.get_json(silent=True) or {}
    try:
        week_number = int(data.get("week_number"))
        points_achieved = float(data.get("points_achieved"))
        points_max = float(data.get("points_max"))
    except (TypeError, ValueError):
        return error("week_number, points_achieved und points_max sind erforderlich und müssen Zahlen sein")

    if points_max <= 0:
        return error("points_max muss positiv sein")
    if points_achieved < 0:
        return error("points_achieved darf nicht negativ sein")
    if points_achieved > points_max:
        return error("points_achieved darf points_max nicht überschreiten")

    existing = Submission.query.filter_by(series_id=series_id, week_number=week_number).first()
    if existing:
        existing.points_achieved = points_achieved
        existing.points_max = points_max
    else:
        db.session.add(
            Submission(
                series_id=series_id,
                week_number=week_number,
                points_achieved=points_achieved,
                points_max=points_max,
            )
        )
    db.session.commit()
    return jsonify(series.modul.to_dict()), 201


@bp.patch("/submissions/<int:submission_id>")
@login_required
def update_submission(submission_id: int):
    submission = _get_owned_submission(submission_id)
    if not submission:
        return error("Abgabe nicht gefunden", 404)

    data = request.get_json(silent=True) or {}
    points_achieved = data.get("points_achieved", submission.points_achieved)
    points_max = data.get("points_max", submission.points_max)
    try:
        points_achieved = float(points_achieved)
        points_max = float(points_max)
    except (TypeError, ValueError):
        return error("points_achieved und points_max müssen Zahlen sein")
    if points_max <= 0:
        return error("points_max muss positiv sein")
    if points_achieved < 0:
        return error("points_achieved darf nicht negativ sein")
    if points_achieved > points_max:
        return error("points_achieved darf points_max nicht überschreiten")

    submission.points_achieved = points_achieved
    submission.points_max = points_max
    if "week_number" in data:
        try:
            submission.week_number = int(data["week_number"])
        except (TypeError, ValueError):
            return error("week_number muss eine ganze Zahl sein")

    db.session.commit()
    return jsonify(submission.series.modul.to_dict())


@bp.delete("/submissions/<int:submission_id>")
@login_required
def delete_submission(submission_id: int):
    submission = _get_owned_submission(submission_id)
    if not submission:
        return error("Abgabe nicht gefunden", 404)
    modul = submission.series.modul
    db.session.delete(submission)
    db.session.commit()
    return jsonify(modul.to_dict())
