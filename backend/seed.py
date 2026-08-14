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
            print("Database already has data - skipping seed.")
            return

        user = User(name="Demo User", email=DEMO_EMAIL)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()

        math = Studiengang(name="Mathematics", user_id=user.id)
        physics = Studiengang(name="Physics", user_id=user.id)
        economics = Studiengang(name="Economics", user_id=user.id)
        db.session.add_all([math, physics, economics])
        db.session.flush()

        calculus = Modul(name="Calculus I", credits=9, user_id=user.id, studiengaenge=[math])
        linalg = Modul(name="Linear Algebra I", credits=9, user_id=user.id, studiengaenge=[math])
        intro_physics = Modul(
            name="Introductory Physics I", credits=8, user_id=user.id, studiengaenge=[physics]
        )
        microecon = Modul(name="Microeconomics", credits=6, user_id=user.id, studiengaenge=[economics])
        language_course = Modul(name="Spanish A1", credits=3, user_id=user.id, studiengaenge=[])  # Other

        db.session.add_all([calculus, linalg, intro_physics, microecon, language_course])
        db.session.flush()

        db.session.add_all(
            [
                GradeAttempt(modul_id=calculus.id, slot=1, kind="numeric", value=1.7),
                GradeAttempt(modul_id=linalg.id, slot=1, kind="numeric", value=1.3),
                GradeAttempt(modul_id=intro_physics.id, slot=1, kind="numeric", value=2.0),
                GradeAttempt(modul_id=language_course.id, slot=1, kind="pass"),
            ]
        )

        problem_set = SubmissionSeries(modul=calculus, name="Problem Set", threshold_percent=50, total_weeks=12)
        programming_exercise = SubmissionSeries(
            modul=calculus, name="Programming Exercise", threshold_percent=50, total_weeks=6
        )
        db.session.add_all([problem_set, programming_exercise])
        db.session.flush()

        for week, (achieved, max_) in enumerate(
            [(8, 10), (7, 10), (9, 10), (6, 10), (8, 10)], start=1
        ):
            db.session.add(
                Submission(series=problem_set, week_number=week, points_achieved=achieved, points_max=max_)
            )
        for week, (achieved, max_) in enumerate([(15, 20), (10, 20)], start=1):
            db.session.add(
                Submission(
                    series=programming_exercise, week_number=week, points_achieved=achieved, points_max=max_
                )
            )

        math_for_physicists = KombiModul(
            name="Math for Physicists",
            credits=14,
            studiengang=physics,
            user_id=user.id,
            source_module=[calculus, linalg],
        )
        db.session.add(math_for_physicists)

        db.session.commit()
        print(f"Seed data created successfully. Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    run()
