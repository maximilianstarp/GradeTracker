"""Populate the database with realistic example data for local exploration
and screenshots. Safe to run multiple times against a fresh database only -
it does not de-duplicate against existing rows.

Usage:
    python seed.py
"""
from app import create_app
from app.models import KombiModul, Modul, Studiengang, SubmissionSeries, Submission, GradeAttempt, db


def run():
    app = create_app()
    with app.app_context():
        if Studiengang.query.first():
            print("Datenbank enthält bereits Daten - Seed übersprungen.")
            return

        mathe = Studiengang(name="Mathematik")
        physik = Studiengang(name="Physik")
        vwl = Studiengang(name="VWL")
        db.session.add_all([mathe, physik, vwl])
        db.session.flush()

        analysis = Modul(name="Analysis I", credits=9, studiengang=mathe)
        linalg = Modul(name="Lineare Algebra I", credits=9, studiengang=mathe)
        experimentalphysik = Modul(name="Experimentalphysik I", credits=8, studiengang=physik)
        mikrooekonomik = Modul(name="Mikroökonomik", credits=6, studiengang=vwl)
        sprachkurs = Modul(name="Spanisch A1", credits=3, studiengang=None)  # Sonstiges

        db.session.add_all([analysis, linalg, experimentalphysik, mikrooekonomik, sprachkurs])
        db.session.flush()

        db.session.add_all(
            [
                GradeAttempt(modul_id=analysis.id, slot=1, kind="numeric", value=1.7),
                GradeAttempt(modul_id=linalg.id, slot=1, kind="numeric", value=1.3),
                GradeAttempt(modul_id=experimentalphysik.id, slot=1, kind="numeric", value=2.0),
                GradeAttempt(modul_id=sprachkurs.id, slot=1, kind="pass"),
            ]
        )

        rechenblatt = SubmissionSeries(modul=analysis, name="Rechenblatt", threshold_percent=50, total_weeks=12)
        programmierblatt = SubmissionSeries(
            modul=analysis, name="Programmierblatt", threshold_percent=50, total_weeks=6
        )
        db.session.add_all([rechenblatt, programmierblatt])
        db.session.flush()

        for week, (achieved, max_) in enumerate(
            [(8, 10), (7, 10), (9, 10), (6, 10), (8, 10)], start=1
        ):
            db.session.add(
                Submission(series=rechenblatt, week_number=week, points_achieved=achieved, points_max=max_)
            )
        for week, (achieved, max_) in enumerate([(15, 20), (10, 20)], start=1):
            db.session.add(
                Submission(series=programmierblatt, week_number=week, points_achieved=achieved, points_max=max_)
            )

        mathe_fuer_physik = KombiModul(
            name="Mathe für Physiker",
            credits=14,
            studiengang=physik,
            source_module=[analysis, linalg],
        )
        db.session.add(mathe_fuer_physik)

        db.session.commit()
        print("Seed-Daten erfolgreich angelegt.")


if __name__ == "__main__":
    run()
