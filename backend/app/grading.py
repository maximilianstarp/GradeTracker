"""Pure, framework-independent grading & progress calculations.

Deliberately kept free of Flask/SQLAlchemy imports so the core domain logic
can be unit-tested in isolation (see tests/test_grading.py) and reused from
anywhere (routes, scripts, a future CLI, ...).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

DEFAULT_THRESHOLD_PERCENT = 50.0


# ---------------------------------------------------------------------------
# Grades (Noten)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GradeAttemptData:
    kind: str  # "numeric" | "pass" | "fail"
    value: Optional[float] = None  # only set when kind == "numeric"


@dataclass(frozen=True)
class FinalGrade:
    """Resolved outcome of a module's (up to 3) grade attempts."""
    status: str  # "numeric" | "passed" | "failed" | "none"
    value: Optional[float] = None  # numeric grade (lower = better), if status == "numeric"

    @property
    def counts_towards_average(self) -> bool:
        return self.status == "numeric"

    @property
    def is_completed(self) -> bool:
        return self.status in ("numeric", "passed", "failed")


def best_grade(attempts: Sequence[GradeAttemptData]) -> FinalGrade:
    """Take the best of up to 3 grade attempts.

    Numeric grades follow the German scale where a *lower* value is better
    (1.0 = best, 5.0 = fail). If any numeric attempt exists, the smallest
    value wins, regardless of pass/fail attempts alongside it. Otherwise, if
    only pass/fail attempts exist, "passed" beats "failed". No attempts ->
    "none".
    """
    numeric_values = [a.value for a in attempts if a.kind == "numeric" and a.value is not None]
    if numeric_values:
        return FinalGrade(status="numeric", value=min(numeric_values))

    if any(a.kind == "pass" for a in attempts):
        return FinalGrade(status="passed")
    if any(a.kind == "fail" for a in attempts):
        return FinalGrade(status="failed")
    return FinalGrade(status="none")


# ---------------------------------------------------------------------------
# Weekly submissions / Klausurzulassung
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubmissionData:
    points_achieved: float
    points_max: float


@dataclass(frozen=True)
class SeriesProgress:
    points_achieved: float
    points_max: float
    percent: Optional[float]  # None if no points_max recorded yet
    threshold_percent: float
    passed: bool
    points_needed: float  # additional points needed against points_max already recorded to hit threshold


def series_progress(
    submissions: Iterable[SubmissionData],
    threshold_percent: float = DEFAULT_THRESHOLD_PERCENT,
) -> SeriesProgress:
    achieved = sum(s.points_achieved for s in submissions)
    maximum = sum(s.points_max for s in submissions)

    if maximum <= 0:
        return SeriesProgress(
            points_achieved=achieved,
            points_max=maximum,
            percent=None,
            threshold_percent=threshold_percent,
            passed=False,
            points_needed=0.0,
        )

    percent = achieved / maximum * 100
    needed_total = threshold_percent / 100 * maximum
    points_needed = max(0.0, needed_total - achieved)

    return SeriesProgress(
        points_achieved=achieved,
        points_max=maximum,
        percent=percent,
        threshold_percent=threshold_percent,
        passed=percent >= threshold_percent,
        points_needed=points_needed,
    )


def module_zulassung(series_progresses: Sequence[SeriesProgress]) -> bool:
    """A module's Klausurzulassung requires every tracked series to pass.

    A module with no series at all is considered "not applicable" -> True,
    so modules without weekly submissions don't show up as blocked.
    """
    if not series_progresses:
        return True
    return all(sp.passed for sp in series_progresses)


# ---------------------------------------------------------------------------
# Credit-weighted average (Notenschnitt)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WeightedEntry:
    credits: float
    grade: FinalGrade


@dataclass(frozen=True)
class WeightedAverageResult:
    average: Optional[float]  # None if no graded (numeric) entries
    graded_credits: float  # credits that count towards the average
    ungraded_pass_credits: float  # credits from pass/fail-passed modules (not part of average)
    total_credits: float


def weighted_average(entries: Sequence[WeightedEntry]) -> WeightedAverageResult:
    numeric_entries = [e for e in entries if e.grade.counts_towards_average]
    graded_credits = sum(e.credits for e in numeric_entries)
    ungraded_pass_credits = sum(
        e.credits for e in entries if e.grade.status == "passed"
    )
    total_credits = sum(e.credits for e in entries if e.grade.is_completed)

    if graded_credits <= 0:
        average = None
    else:
        average = sum(e.credits * e.grade.value for e in numeric_entries) / graded_credits

    return WeightedAverageResult(
        average=average,
        graded_credits=graded_credits,
        ungraded_pass_credits=ungraded_pass_credits,
        total_credits=total_credits,
    )


# ---------------------------------------------------------------------------
# Kombi-Module (combined modules)
# ---------------------------------------------------------------------------

def _is_passing(grade: FinalGrade) -> bool:
    """Whether a source module's final grade counts as passed: an explicit
    "passed" pass/fail result, or a numeric grade at/better than the German
    4.0 pass threshold (grades above 4.0 are a failing numeric grade, not
    just "not yet graded")."""
    if grade.status == "passed":
        return True
    if grade.status == "numeric" and grade.value is not None:
        return grade.value <= 4.0
    return False


def _is_failing(grade: FinalGrade) -> bool:
    if grade.status == "failed":
        return True
    if grade.status == "numeric" and grade.value is not None:
        return grade.value > 4.0
    return False


def kombimodul_grade(source_final_grades: Sequence[FinalGrade], graded: bool = True) -> FinalGrade:
    """A Kombi-Modul's grade combines its source modules' final grades.

    Graded ("benotet", the default): the arithmetic mean of the source
    modules' numeric grades. A source module that isn't itself graded (or
    is graded but was simply recorded as pass/fail) doesn't block this -
    it's dropped from the average once it's passed, exactly like it would
    be dropped from a program's own credit-weighted average. It only blocks
    the combined grade ("none") while still open, and turns the whole
    combined module "failed" if it fails outright - same as any numeric
    source scoring worse than 4.0. A single source module is allowed - the
    "average" of one grade is just that grade, which is exactly right for
    re-crediting one module under different credits via its own combined
    module.

    Ungraded ("unbenotet"): pass/fail instead of a numeric average - some
    programs list a combined module (e.g. "Math for Physicists") as
    unbenotet even though its source modules (Analysis, Linear Algebra) are
    each individually graded. "Failed" if any source module has failed
    outright, "passed" once every source module has passed, "none" while
    still open.
    """
    if not source_final_grades:
        return FinalGrade(status="none")

    if not graded:
        if any(_is_failing(g) for g in source_final_grades):
            return FinalGrade(status="failed")
        if all(_is_passing(g) for g in source_final_grades):
            return FinalGrade(status="passed")
        return FinalGrade(status="none")

    if any(_is_failing(g) for g in source_final_grades):
        return FinalGrade(status="failed")

    numeric_grades = [g.value for g in source_final_grades if g.status == "numeric"]
    non_numeric = [g for g in source_final_grades if g.status != "numeric"]
    if not numeric_grades or any(g.status != "passed" for g in non_numeric):
        return FinalGrade(status="none")

    return FinalGrade(status="numeric", value=sum(numeric_grades) / len(numeric_grades))
