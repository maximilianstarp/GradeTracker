"""SQLAlchemy models for the Grade Tracker domain.

User owns Studiengang / Modul / KombiModul directly (each has its own
user_id) so a Modul without any Studiengang ("Sonstiges") still has an
owner. Modul <-> Studiengang is many-to-many: a module can be credited in
several programs at once, each accreditation independent - the same
principle already used for KombiModul's source modules.

Studiengang (program) <-> Modul (module) -> GradeAttempt / SubmissionSeries -> Submission
KombiModul combines several Module into one graded, credited unit inside a Studiengang.
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


kombimodul_module = db.Table(
    "kombimodul_module",
    db.Column("kombimodul_id", db.Integer, db.ForeignKey("kombi_modul.id", ondelete="CASCADE"), primary_key=True),
    db.Column("modul_id", db.Integer, db.ForeignKey("modul.id", ondelete="CASCADE"), primary_key=True),
)

modul_studiengang = db.Table(
    "modul_studiengang",
    db.Column("modul_id", db.Integer, db.ForeignKey("modul.id", ondelete="CASCADE"), primary_key=True),
    db.Column("studiengang_id", db.Integer, db.ForeignKey("studiengang.id", ondelete="CASCADE"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "email": self.email}


class Studiengang(db.Model):
    __tablename__ = "studiengang"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    module = db.relationship(
        "Modul", secondary=modul_studiengang, back_populates="studiengaenge", lazy="selectin"
    )
    kombi_module = db.relationship("KombiModul", back_populates="studiengang", lazy="selectin")

    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_studiengang_user_name"),)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


class Modul(db.Model):
    __tablename__ = "modul"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    studiengaenge = db.relationship(
        "Studiengang", secondary=modul_studiengang, back_populates="module", lazy="selectin"
    )
    grade_attempts = db.relationship(
        "GradeAttempt", back_populates="modul", cascade="all, delete-orphan", lazy="selectin",
        order_by="GradeAttempt.slot",
    )
    series = db.relationship(
        "SubmissionSeries", back_populates="modul", cascade="all, delete-orphan", lazy="selectin",
    )

    def to_dict(self, include_progress: bool = True) -> dict:
        from app import grading

        data = {
            "id": self.id,
            "name": self.name,
            "credits": self.credits,
            "studiengang_ids": [s.id for s in self.studiengaenge],
            "studiengaenge": [{"id": s.id, "name": s.name} for s in self.studiengaenge],
            "grade_attempts": [g.to_dict() for g in self.grade_attempts],
        }

        final = self.final_grade()
        data["final_grade"] = {"status": final.status, "value": final.value}

        if include_progress:
            data["series"] = [s.to_dict() for s in self.series]
            progresses = [s.progress() for s in self.series]
            data["zulassung"] = grading.module_zulassung(progresses)

        return data

    def final_grade(self):
        from app import grading

        attempts = [
            grading.GradeAttemptData(kind=g.kind, value=g.value) for g in self.grade_attempts
        ]
        return grading.best_grade(attempts)


class GradeAttempt(db.Model):
    __tablename__ = "grade_attempt"

    id = db.Column(db.Integer, primary_key=True)
    modul_id = db.Column(db.Integer, db.ForeignKey("modul.id", ondelete="CASCADE"), nullable=False)
    slot = db.Column(db.Integer, nullable=False, default=1)  # 1..3
    kind = db.Column(db.String(10), nullable=False)  # "numeric" | "pass" | "fail"
    value = db.Column(db.Float, nullable=True)  # only for kind == "numeric"

    modul = db.relationship("Modul", back_populates="grade_attempts")

    __table_args__ = (
        db.CheckConstraint("slot >= 1 AND slot <= 3", name="ck_grade_attempt_slot_range"),
        db.CheckConstraint("kind IN ('numeric', 'pass', 'fail')", name="ck_grade_attempt_kind"),
        db.UniqueConstraint("modul_id", "slot", name="uq_grade_attempt_modul_slot"),
    )

    def to_dict(self) -> dict:
        return {"id": self.id, "slot": self.slot, "kind": self.kind, "value": self.value}


class SubmissionSeries(db.Model):
    __tablename__ = "submission_series"

    id = db.Column(db.Integer, primary_key=True)
    modul_id = db.Column(db.Integer, db.ForeignKey("modul.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    threshold_percent = db.Column(db.Float, nullable=False, default=50.0)
    total_weeks = db.Column(db.Integer, nullable=True)

    modul = db.relationship("Modul", back_populates="series")
    submissions = db.relationship(
        "Submission", back_populates="series", cascade="all, delete-orphan", lazy="selectin",
        order_by="Submission.week_number",
    )

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "modul_id": self.modul_id,
            "name": self.name,
            "threshold_percent": self.threshold_percent,
            "total_weeks": self.total_weeks,
            "submissions": [s.to_dict() for s in self.submissions],
        }
        p = self.progress()
        data["progress"] = {
            "points_achieved": p.points_achieved,
            "points_max": p.points_max,
            "percent": p.percent,
            "passed": p.passed,
            "points_needed": p.points_needed,
        }
        return data

    def progress(self):
        from app import grading

        subs = [grading.SubmissionData(s.points_achieved, s.points_max) for s in self.submissions]
        return grading.series_progress(subs, self.threshold_percent)


class Submission(db.Model):
    __tablename__ = "submission"

    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey("submission_series.id", ondelete="CASCADE"), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    points_achieved = db.Column(db.Float, nullable=False, default=0)
    points_max = db.Column(db.Float, nullable=False)

    series = db.relationship("SubmissionSeries", back_populates="submissions")

    __table_args__ = (
        db.UniqueConstraint("series_id", "week_number", name="uq_submission_series_week"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "series_id": self.series_id,
            "week_number": self.week_number,
            "points_achieved": self.points_achieved,
            "points_max": self.points_max,
        }


class KombiModul(db.Model):
    __tablename__ = "kombi_modul"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Float, nullable=False)
    studiengang_id = db.Column(db.Integer, db.ForeignKey("studiengang.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    studiengang = db.relationship("Studiengang", back_populates="kombi_module")
    source_module = db.relationship("Modul", secondary=kombimodul_module, lazy="selectin")

    def to_dict(self) -> dict:
        from app import grading

        source_finals = [m.final_grade() for m in self.source_module]
        final = grading.kombimodul_grade(source_finals)
        return {
            "id": self.id,
            "name": self.name,
            "credits": self.credits,
            "studiengang_id": self.studiengang_id,
            "source_module_ids": [m.id for m in self.source_module],
            "source_module": [{"id": m.id, "name": m.name} for m in self.source_module],
            "final_grade": {"status": final.status, "value": final.value},
        }
