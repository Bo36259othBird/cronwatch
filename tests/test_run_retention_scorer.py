"""Tests for cronwatch.run_retention_scorer."""
from __future__ import annotations

import datetime
import pytest

from cronwatch.store import JobStore
from cronwatch.run_retention_scorer import RetentionScore, RetentionScorer


UTC = datetime.timezone.utc


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def scorer(store):
    return RetentionScorer(store)


def _add_run(
    store: JobStore,
    job: str,
    exit_code: int = 0,
    duration_s: int = 60,
    finished: bool = True,
) -> int:
    now = datetime.datetime.now(UTC)
    start = now - datetime.timedelta(seconds=duration_s)
    run_id = store.record_start(job, start)
    if finished:
        store.record_finish(run_id, exit_code, now)
    return run_id


# ---------------------------------------------------------------------------
# RetentionScore helpers
# ---------------------------------------------------------------------------

def test_is_high_priority_true():
    rs = RetentionScore(run_id=1, job_name="j", score=0.8, reasons=["failure"])
    assert rs.is_high_priority() is True


def test_is_high_priority_false():
    rs = RetentionScore(run_id=2, job_name="j", score=0.1, reasons=[])
    assert rs.is_high_priority() is False


def test_is_high_priority_custom_threshold():
    rs = RetentionScore(run_id=3, job_name="j", score=0.5, reasons=[])
    assert rs.is_high_priority(threshold=0.4) is True
    assert rs.is_high_priority(threshold=0.6) is False


# ---------------------------------------------------------------------------
# RetentionScorer.score_job
# ---------------------------------------------------------------------------

def test_score_job_empty_returns_empty(scorer):
    assert scorer.score_job("missing") == []


def test_score_job_returns_retention_score_instances(store, scorer):
    _add_run(store, "backup", exit_code=0, duration_s=30)
    results = scorer.score_job("backup")
    assert len(results) == 1
    assert isinstance(results[0], RetentionScore)


def test_failure_run_has_higher_score_than_success(store, scorer):
    _add_run(store, "job", exit_code=0, duration_s=10)
    _add_run(store, "job", exit_code=1, duration_s=10)
    scores = {rs.run_id: rs.score for rs in scorer.score_job("job")}
    success_id, failure_id = list(scores.keys())
    # failure was added second so it appears first (newest first)
    assert scores[failure_id] > scores[success_id]


def test_long_duration_increases_score(store, scorer):
    short_id = _add_run(store, "job", exit_code=0, duration_s=30)
    long_id = _add_run(store, "job", exit_code=0, duration_s=7200)
    scores = {rs.run_id: rs.score for rs in scorer.score_job("job")}
    assert scores[long_id] > scores[short_id]


def test_incomplete_run_gets_score(store, scorer):
    _add_run(store, "job", finished=False)
    results = scorer.score_job("job")
    assert results[0].score > 0.0
    assert "incomplete" in results[0].reasons


# ---------------------------------------------------------------------------
# RetentionScorer.high_priority_ids
# ---------------------------------------------------------------------------

def test_high_priority_ids_returns_only_high_scorers(store, scorer):
    _add_run(store, "j", exit_code=0, duration_s=10)   # low score
    _add_run(store, "j", exit_code=2, duration_s=10)   # failure -> high score
    ids = scorer.high_priority_ids("j", threshold=0.4)
    assert len(ids) == 1


def test_high_priority_ids_empty_when_all_low(store, scorer):
    _add_run(store, "j", exit_code=0, duration_s=10)
    assert scorer.high_priority_ids("j", threshold=0.9) == []
