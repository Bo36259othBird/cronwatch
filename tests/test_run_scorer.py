"""Tests for cronwatch.run_scorer."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_scorer import RunScorer, JobScore


DT_BASE = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def scorer(store):
    return RunScorer(store, window=20)


def _add_run(store, job, exit_code, offset_hours=0, duration_secs=10):
    started = DT_BASE - timedelta(hours=offset_hours)
    finished = started + timedelta(seconds=duration_secs)
    run_id = store.record_start(job, started)
    store.record_finish(run_id, finished, exit_code)
    return run_id


def test_score_no_runs_returns_none(scorer):
    assert scorer.score("missing_job") is None


def test_score_returns_job_score_instance(store, scorer):
    _add_run(store, "backup", 0, offset_hours=1)
    result = scorer.score("backup")
    assert isinstance(result, JobScore)


def test_score_all_successes_high_score(store, scorer):
    for i in range(10):
        _add_run(store, "backup", 0, offset_hours=i + 1)
    result = scorer.score("backup")
    assert result is not None
    assert result.score >= 75
    assert result.success_rate == 1.0


def test_score_all_failures_low_score(store, scorer):
    for i in range(10):
        _add_run(store, "nightly", 1, offset_hours=i + 1)
    result = scorer.score("nightly")
    assert result is not None
    assert result.score <= 40
    assert result.success_rate == 0.0


def test_grade_a_for_perfect_score(store, scorer):
    for i in range(5):
        _add_run(store, "sync", 0, offset_hours=i + 1, duration_secs=10)
    result = scorer.score("sync")
    assert result is not None
    assert result.grade in ("A", "B")


def test_grade_f_for_low_score(store, scorer):
    for i in range(5):
        _add_run(store, "broken", 2, offset_hours=i + 1)
    result = scorer.score("broken")
    assert result is not None
    assert result.grade == "F"


def test_has_recent_run_false_when_old(store, scorer):
    _add_run(store, "old_job", 0, offset_hours=48)
    result = scorer.score("old_job")
    assert result is not None
    assert result.has_recent_run is False


def test_has_recent_run_true_when_fresh(store, scorer):
    _add_run(store, "fresh_job", 0, offset_hours=1)
    result = scorer.score("fresh_job")
    assert result is not None
    assert result.has_recent_run is True


def test_grade_from_score_boundaries():
    assert JobScore.grade_from_score(100) == "A"
    assert JobScore.grade_from_score(90) == "A"
    assert JobScore.grade_from_score(89) == "B"
    assert JobScore.grade_from_score(75) == "B"
    assert JobScore.grade_from_score(74) == "C"
    assert JobScore.grade_from_score(60) == "C"
    assert JobScore.grade_from_score(59) == "D"
    assert JobScore.grade_from_score(39) == "F"
