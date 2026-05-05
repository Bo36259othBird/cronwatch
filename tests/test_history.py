"""Tests for cronwatch.history."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from cronwatch.store import JobStore
from cronwatch.history import HistoryAnalyzer, JobTrend


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def analyzer(store):
    return HistoryAnalyzer(store)


def _add_run(store, name, exit_code=0, minutes_ago=10, duration_seconds=5):
    started = datetime.utcnow() - timedelta(minutes=minutes_ago)
    finished = started + timedelta(seconds=duration_seconds)
    run_id = store.record_start(name, started)
    store.record_finish(run_id, exit_code, finished)
    return run_id


def test_trend_no_runs(analyzer):
    t = analyzer.trend("missing_job")
    assert t.total_runs == 0
    assert t.failure_rate == 0.0
    assert t.avg_duration_seconds is None
    assert t.last_run_at is None


def test_trend_counts_runs(store, analyzer):
    _add_run(store, "backup", exit_code=0)
    _add_run(store, "backup", exit_code=0)
    _add_run(store, "backup", exit_code=1)
    t = analyzer.trend("backup")
    assert t.total_runs == 3
    assert t.successful_runs == 2
    assert t.failed_runs == 1


def test_trend_failure_rate(store, analyzer):
    _add_run(store, "job", exit_code=1)
    _add_run(store, "job", exit_code=1)
    _add_run(store, "job", exit_code=0)
    _add_run(store, "job", exit_code=0)
    t = analyzer.trend("job")
    assert t.failure_rate == pytest.approx(0.5)


def test_trend_is_degrading(store, analyzer):
    for _ in range(3):
        _add_run(store, "flaky", exit_code=1)
    _add_run(store, "flaky", exit_code=0)
    t = analyzer.trend("flaky")
    assert t.is_degrading is True


def test_trend_not_degrading(store, analyzer):
    for _ in range(9):
        _add_run(store, "stable", exit_code=0)
    _add_run(store, "stable", exit_code=1)
    t = analyzer.trend("stable")
    assert t.is_degrading is False


def test_trend_avg_duration(store, analyzer):
    _add_run(store, "timed", exit_code=0, duration_seconds=10)
    _add_run(store, "timed", exit_code=0, duration_seconds=20)
    t = analyzer.trend("timed")
    assert t.avg_duration_seconds == pytest.approx(15.0)


def test_all_trends_returns_one_per_job(store, analyzer):
    _add_run(store, "a")
    _add_run(store, "b")
    trends = analyzer.all_trends(["a", "b", "c"])
    assert len(trends) == 3
    assert {tr.job_name for tr in trends} == {"a", "b", "c"}
