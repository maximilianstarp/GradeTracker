from flask import Blueprint, g, jsonify

from app import grading
from app.auth import login_required
from app.models import KombiModul, Modul, Studiengang

bp = Blueprint("stats", __name__, url_prefix="/api/stats")


def _bucket_stats(module: list[Modul], kombi_module: list[KombiModul]) -> dict:
    entries = [
        grading.WeightedEntry(credits=m.credits, grade=m.final_grade()) for m in module
    ]
    entries += [
        grading.WeightedEntry(credits=k.credits, grade=grading.kombimodul_grade([m.final_grade() for m in k.source_module]))
        for k in kombi_module
    ]
    result = grading.weighted_average(entries)

    open_zulassung = []
    for m in module:
        progresses = [s.progress() for s in m.series]
        if not grading.module_zulassung(progresses):
            open_zulassung.append({"modul_id": m.id, "modul_name": m.name})

    return {
        "average": result.average,
        "graded_credits": result.graded_credits,
        "ungraded_pass_credits": result.ungraded_pass_credits,
        "total_credits": result.total_credits,
        "module_count": len(module) + len(kombi_module),
        "open_zulassung": open_zulassung,
    }


@bp.get("/overview")
@login_required
def overview():
    user_id = g.current_user.id
    studiengaenge = Studiengang.query.filter_by(user_id=user_id).order_by(Studiengang.name).all()

    per_studiengang = []
    for sg in studiengaenge:
        stats = _bucket_stats(sg.module, sg.kombi_module)
        per_studiengang.append({"id": sg.id, "name": sg.name, **stats})

    sonstige_module = Modul.query.filter(
        Modul.user_id == user_id, ~Modul.studiengaenge.any()
    ).all()
    sonstiges = {"id": None, "name": "Other", **_bucket_stats(sonstige_module, [])}

    # Every Modul and KombiModul row is counted exactly once here, regardless of
    # whether a Modul also feeds into a KombiModul or several Studiengänge
    # elsewhere - each row represents its own credit accreditation.
    all_module = Modul.query.filter_by(user_id=user_id).all()
    all_kombi = KombiModul.query.filter_by(user_id=user_id).all()
    overall = _bucket_stats(all_module, all_kombi)

    return jsonify(
        {
            "studiengaenge": per_studiengang,
            "sonstiges": sonstiges,
            "overall": overall,
        }
    )
