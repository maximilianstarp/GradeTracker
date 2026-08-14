"""Populate the database with a demo user and realistic example data for
local exploration and screenshots. Safe to run multiple times against a
fresh database only - it does not de-duplicate against existing rows.

Usage:
    python seed.py
"""
from app import create_app
from app.models import KombiModul, Modul, Studiengang, SubmissionSeries, Submission, GradeAttempt, User, db

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"


def run():
    app = create_app()
    with app.app_context():
        if User.query.first():
            print("Datenbank enthält bereits Daten - Seed übersprungen.")
            return

        user = User(name="Demo Nutzer", email=DEMO_EMAIL)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()

        mathe = Studiengang(name="Mathematik", user_id=user.id)
        physik = Studiengang(name="Physik", user_id=user.id)
        vwl = Studiengang(name="VWL", user_id=user.id)
        db.session.add_all([mathe, physik, vwl])
        db.session.flush()

        analysis = Modul(name="Analysis I", credits=9, user_id=user.id, studiengaenge=[mathe])
        linalg = Modul(name="Lineare Algebra I", credits=9, user_id=user.id, studiengaenge=[mathe])
        experimentalphysik = Modul(
            name="Experimentalphysik I", credits=8, user_id=user.id, studiengaenge=[physik]
        )
        mikrooekonomik = Modul(name="Mikroökonomik", credits=6, user_id=user.id, studiengaenge=[vwl])
        sprachkurs = Modul(name="Spanisch A1", credits=3, user_id=user.id, studiengaenge=[])  # Sonstiges

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
            user_id=user.id,
            source_module=[analysis, linalg],
        )
        db.session.add(mathe_fuer_physik)

        db.session.commit()
        print(f"Seed-Daten erfolgreich angelegt. Demo-Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    run()
