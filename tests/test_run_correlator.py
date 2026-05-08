"""Tests for RunCorrelator and correlation_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_correlator import RunCorrelator, CorrelatedPair
from cronwatch.correlation_formatter import format_correlation


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def correlator(store):
    return RunCorrelator(store, window_seconds=30)


def _utc(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


def _add_run(store, job: str, started: datetime, exit_code: int = 0) -> None:
    run_id = store.record_start(job, started)
    store.record_finish(run_id, exit_code=exit_code, finished_at=started)


# --- RunCorrelator ---

def test_correlate_no_runs_returns_zero_overlap(correlator):
    pair = correlator.correlate("job_a", "job_b")
    assert pair.overlap_count == 0
    assert pair.co_failure_count == 0


def test_correlate_overlapping_successes(store, correlator):
    _add_run(store, "job_a", _utc(10, 0), exit_code=0)
    _add_run(store, "job_b", _utc(10, 0), exit_code=0)
    pair = correlator.correlate("job_a", "job_b")
    assert pair.overlap_count == 1
    assert pair.co_failure_count == 0


def test_correlate_co_failure(store, correlator):
    _add_run(store, "job_a", _utc(10, 0), exit_code=1)
    _add_run(store, "job_b", _utc(10, 0), exit_code=2)
    pair = correlator.correlate("job_a", "job_b")
    assert pair.co_failure_count == 1
    assert pair.is_correlated is True


def test_correlate_outside_window_not_counted(store, correlator):
    _add_run(store, "job_a", _utc(10, 0), exit_code=1)
    _add_run(store, "job_b", _utc(10, 5), exit_code=1)  # 5 min apart > 30 s
    pair = correlator.correlate("job_a", "job_b")
    assert pair.overlap_count == 0


def test_co_failure_rate_calculation():
    pair = CorrelatedPair("a", "b", overlap_count=4, co_failure_count=2)
    assert pair.co_failure_rate == 0.5


def test_co_failure_rate_zero_overlap():
    pair = CorrelatedPair("a", "b", overlap_count=0, co_failure_count=0)
    assert pair.co_failure_rate == 0.0


def test_correlate_all_returns_all_pairs(store, correlator):
    pairs = correlator.correlate_all(["job_a", "job_b", "job_c"])
    assert len(pairs) == 3  # (a,b), (a,c), (b,c)


# --- correlation_formatter ---

def _pair(correlated: bool = False) -> CorrelatedPair:
    return CorrelatedPair(
        job_a="backup",
        job_b="cleanup",
        overlap_count=4,
        co_failure_count=3 if correlated else 0,
    )


def test_text_contains_job_names():
    out = format_correlation([_pair()], fmt="text")
    assert "backup" in out
    assert "cleanup" in out


def test_text_flags_correlated_pair():
    out = format_correlation([_pair(correlated=True)], fmt="text")
    assert "CORRELATED" in out


def test_text_empty_list():
    out = format_correlation([], fmt="text")
    assert "No correlation" in out


def test_json_is_valid():
    out = format_correlation([_pair()], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["job_a"] == "backup"
