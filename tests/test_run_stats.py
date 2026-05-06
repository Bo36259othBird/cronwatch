"""Tests for cronwatch.run_stats."""

from __future__ import annotations

import pytest

from cronwatch.store import JobStore
from cronwatch.run_stats import RunStats, RunStatsCollector


@pytest.fixture()
def store(tmp_path):
    db = tmp_path / "test.db"
    s = JobStore(str(db))
    return s


@pytest.fixture()
def collector(store):
    return RunStatsCollector(store)


def _add_run(store: JobStore, job: str, duration: float | None, success: bool = True) -> None:
    run_id = store.record_start(job)
    store.record_finish(run_id, success=success, duration_seconds=duration)


# ---------------------------------------------------------------------------
# RunStatsCollector.collect
# ---------------------------------------------------------------------------

def test_collect_no_runs_returns_none_fields(collector):
    stats = collector.collect("backup")
    assert stats.run_count == 0
    assert stats.avg_duration is None
    assert stats.median_duration is None
    assert stats.stddev_duration is None


def test_collect_counts_runs(store, collector):
    for d in [10.0, 20.0, 30.0]:
        _add_run(store, "backup", d)
    stats = collector.collect("backup")
    assert stats.run_count == 3


def test_collect_avg_duration(store, collector):
    for d in [10.0, 20.0, 30.0]:
        _add_run(store, "backup", d)
    stats = collector.collect("backup")
    assert stats.avg_duration == pytest.approx(20.0)


def test_collect_min_max(store, collector):
    for d in [5.0, 15.0, 25.0]:
        _add_run(store, "backup", d)
    stats = collector.collect("backup")
    assert stats.min_duration == pytest.approx(5.0)
    assert stats.max_duration == pytest.approx(25.0)


def test_collect_ignores_runs_without_duration(store, collector):
    _add_run(store, "backup", None)
    _add_run(store, "backup", 10.0)
    stats = collector.collect("backup")
    assert stats.run_count == 2
    assert stats.avg_duration == pytest.approx(10.0)


def test_collect_single_run_stddev_is_zero(store, collector):
    _add_run(store, "backup", 42.0)
    stats = collector.collect("backup")
    assert stats.stddev_duration == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# RunStats.is_stable
# ---------------------------------------------------------------------------

def test_is_stable_low_variance():
    stats = RunStats(
        job_name="j", run_count=5,
        avg_duration=100.0, median_duration=100.0,
        stddev_duration=5.0, min_duration=90.0, max_duration=110.0,
    )
    assert stats.is_stable() is True


def test_is_not_stable_high_variance():
    stats = RunStats(
        job_name="j", run_count=5,
        avg_duration=100.0, median_duration=100.0,
        stddev_duration=50.0, min_duration=50.0, max_duration=150.0,
    )
    assert stats.is_stable() is False


def test_is_stable_when_avg_is_none():
    stats = RunStats(
        job_name="j", run_count=0,
        avg_duration=None, median_duration=None,
        stddev_duration=None, min_duration=None, max_duration=None,
    )
    assert stats.is_stable() is True
