import pytest

from app.grading import (
    GradeAttemptData,
    SubmissionData,
    WeightedEntry,
    best_grade,
    kombimodul_grade,
    module_zulassung,
    series_progress,
    weighted_average,
)


class TestBestGrade:
    def test_no_attempts(self):
        assert best_grade([]).status == "none"

    def test_takes_smallest_numeric_value(self):
        attempts = [
            GradeAttemptData(kind="numeric", value=2.3),
            GradeAttemptData(kind="numeric", value=1.7),
            GradeAttemptData(kind="numeric", value=3.0),
        ]
        result = best_grade(attempts)
        assert result.status == "numeric"
        assert result.value == 1.7

    def test_pass_only(self):
        attempts = [GradeAttemptData(kind="pass")]
        result = best_grade(attempts)
        assert result.status == "passed"
        assert result.counts_towards_average is False

    def test_fail_only(self):
        attempts = [GradeAttemptData(kind="fail")]
        assert best_grade(attempts).status == "failed"

    def test_numeric_wins_over_pass_fail(self):
        attempts = [GradeAttemptData(kind="fail"), GradeAttemptData(kind="numeric", value=2.0)]
        result = best_grade(attempts)
        assert result.status == "numeric"
        assert result.value == 2.0


class TestSeriesProgress:
    def test_no_submissions_yet(self):
        result = series_progress([])
        assert result.percent is None
        assert result.passed is False

    def test_above_threshold(self):
        subs = [SubmissionData(8, 10), SubmissionData(6, 10)]
        result = series_progress(subs, threshold_percent=50)
        assert result.points_achieved == 14
        assert result.points_max == 20
        assert result.percent == 70
        assert result.passed is True
        assert result.points_needed == 0

    def test_below_threshold_points_needed(self):
        subs = [SubmissionData(2, 10), SubmissionData(3, 10)]
        result = series_progress(subs, threshold_percent=50)
        assert result.percent == 25
        assert result.passed is False
        # need 50% of 20 = 10, have 5 -> need 5 more
        assert result.points_needed == 5

    def test_custom_threshold(self):
        subs = [SubmissionData(6, 10)]
        result = series_progress(subs, threshold_percent=60)
        assert result.percent == 60
        assert result.passed is True


class TestModuleZulassung:
    def test_no_series_defaults_true(self):
        assert module_zulassung([]) is True

    def test_all_series_must_pass(self):
        passing = series_progress([SubmissionData(6, 10)], 50)
        failing = series_progress([SubmissionData(2, 10)], 50)
        assert module_zulassung([passing, passing]) is True
        assert module_zulassung([passing, failing]) is False


class TestWeightedAverage:
    def test_simple_credit_weighting(self):
        entries = [
            WeightedEntry(credits=9, grade=best_grade([GradeAttemptData("numeric", 1.3)])),
            WeightedEntry(credits=6, grade=best_grade([GradeAttemptData("numeric", 2.0)])),
        ]
        result = weighted_average(entries)
        expected = (9 * 1.3 + 6 * 2.0) / 15
        assert result.average == pytest.approx(expected)
        assert result.graded_credits == 15
        assert result.total_credits == 15

    def test_pass_fail_excluded_from_average_but_counted_in_credits(self):
        entries = [
            WeightedEntry(credits=9, grade=best_grade([GradeAttemptData("numeric", 1.3)])),
            WeightedEntry(credits=3, grade=best_grade([GradeAttemptData("pass")])),
        ]
        result = weighted_average(entries)
        assert result.average == pytest.approx(1.3)
        assert result.graded_credits == 9
        assert result.ungraded_pass_credits == 3
        assert result.total_credits == 12

    def test_no_graded_entries_returns_none_average(self):
        entries = [WeightedEntry(credits=3, grade=best_grade([GradeAttemptData("pass")]))]
        result = weighted_average(entries)
        assert result.average is None


class TestKombimodulGrade:
    def test_averages_two_source_modules(self):
        analysis = best_grade([GradeAttemptData("numeric", 1.0)])
        linalg = best_grade([GradeAttemptData("numeric", 2.0)])
        result = kombimodul_grade([analysis, linalg])
        assert result.status == "numeric"
        assert result.value == pytest.approx(1.5)

    def test_missing_grade_yields_none(self):
        analysis = best_grade([GradeAttemptData("numeric", 1.0)])
        linalg = best_grade([])
        result = kombimodul_grade([analysis, linalg])
        assert result.status == "none"

    def test_no_sources(self):
        assert kombimodul_grade([]).status == "none"

    def test_single_source_module(self):
        """A single source module is allowed - averaging one grade is just
        that grade, which is exactly right for re-crediting a module under
        different credits via its own combined module."""
        analysis = best_grade([GradeAttemptData("numeric", 1.7)])
        result = kombimodul_grade([analysis])
        assert result.status == "numeric"
        assert result.value == pytest.approx(1.7)

    def test_a_passed_non_numeric_source_is_dropped_from_the_average(self):
        """A graded combined module with one graded and one not-graded (but
        passed) source module: the average is over the graded source(s)
        only, the passed-but-non-numeric one doesn't block it."""
        analysis = best_grade([GradeAttemptData("numeric", 2.0)])
        language_course = best_grade([GradeAttemptData("pass")])
        result = kombimodul_grade([analysis, language_course])
        assert result.status == "numeric"
        assert result.value == pytest.approx(2.0)

    def test_a_still_open_non_numeric_source_still_blocks_the_average(self):
        analysis = best_grade([GradeAttemptData("numeric", 2.0)])
        language_course = best_grade([])  # not yet passed or failed
        result = kombimodul_grade([analysis, language_course])
        assert result.status == "none"

    def test_a_failed_non_numeric_source_fails_the_whole_combined_module(self):
        analysis = best_grade([GradeAttemptData("numeric", 2.0)])
        language_course = best_grade([GradeAttemptData("fail")])
        result = kombimodul_grade([analysis, language_course])
        assert result.status == "failed"

    def test_all_sources_passed_but_none_numeric_yields_none(self):
        """Nothing to average - a graded combined module can't produce a
        number out of thin air just because its sources all passed."""
        a = best_grade([GradeAttemptData("pass")])
        b = best_grade([GradeAttemptData("pass")])
        result = kombimodul_grade([a, b])
        assert result.status == "none"


class TestKombimodulGradeUngraded:
    def test_passed_once_all_sources_pass(self):
        analysis = best_grade([GradeAttemptData("numeric", 1.7)])  # numeric but <=4.0 passes
        linalg = best_grade([GradeAttemptData("pass")])
        result = kombimodul_grade([analysis, linalg], graded=False)
        assert result.status == "passed"
        assert result.value is None

    def test_open_while_a_source_is_still_incomplete(self):
        analysis = best_grade([GradeAttemptData("numeric", 1.7)])
        linalg = best_grade([])  # no attempts yet
        result = kombimodul_grade([analysis, linalg], graded=False)
        assert result.status == "none"

    def test_failed_if_a_source_fails_outright(self):
        analysis = best_grade([GradeAttemptData("numeric", 1.7)])
        linalg = best_grade([GradeAttemptData("fail")])
        result = kombimodul_grade([analysis, linalg], graded=False)
        assert result.status == "failed"

    def test_failed_if_a_source_has_a_failing_numeric_grade(self):
        analysis = best_grade([GradeAttemptData("numeric", 1.7)])
        linalg = best_grade([GradeAttemptData("numeric", 4.3)])  # > 4.0 = failed
        result = kombimodul_grade([analysis, linalg], graded=False)
        assert result.status == "failed"

    def test_no_sources_is_none(self):
        assert kombimodul_grade([], graded=False).status == "none"
