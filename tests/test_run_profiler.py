"""Tests for RunProfiler."""
from __future__ import annotations

import datetime
import pytest

from cronwatch.store import JobStore
from cronwatch.run_profiler import RunProfiler, RunProfile


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def profiler(store):
    return RunProfiler(store)


def _utc(offset_seconds: float = 0) -> datetime.datetime:
    return datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc) + \
           datetime.timedelta(seconds=offset_seconds)


def _add_run(store: JobStore, job: str, duration: float, success: bool = True) -> None:
    run_id = store.record_start(job, _utc())
    store.record_finish(run_id, _utc(duration), exit_code=0 if success else 1)


def test_profile_no_runs_returns_none_fields(store, profiler):
    profile = profiler.profile("backup")
    assert profile.run_count == 0
    assert profile.p50 is None
    assert profile.p95 is None
    assert profile.mean is None


def test_profile_returns_run_profile_instance(store, profiler):
    _add_run(store, "backup", 10.0)
    result = profiler.profile("backup")
    assert isinstance(result, RunProfile)


def test_profile_single_run_all_percentiles_equal(store, profiler):
    _add_run(store, "backup", 30.0)
    p = profiler.profile("backup")
    assert p.p50 == pytest.approx(30.0)
    assert p.p95 == pytest.approx(30.0)
    assert p.p99 == pytest.approx(30.0)


def test_profile_counts_runs(store, profiler):
    for d in [5.0, 10.0, 15.0, 20.0]:
        _add_run(store, "sync", d)
    p = profiler.profile("sync")
    assert p.run_count == 4


def test_profile_mean_is_correct(store, profiler):
    for d in [10.0, 20.0, 30.0]:
        _add_run(store, "sync", d)
    p = profiler.profile("sync")
    assert p.mean == pytest.approx(20.0)


def test_is_outlier_detects_slow_run(store, profiler):
    for d in [10.0, 10.0, 10.0, 10.0, 10.0]:
        _add_run(store, "job", d)
    p = profiler.profile("job")
    # stddev is 0 for identical values — not an outlier
    assert not p.is_outlier(10.0)


def test_is_outlier_with_variance(store, profiler):
    for d in [10.0, 12.0, 11.0, 9.0, 10.5]:
        _add_run(store, "job", d)
    p = profiler.profile("job")
    assert p.is_outlier(100.0)  # wildly outside normal range
    assert not p.is_outlier(11.0)


def test_profile_ignores_incomplete_runs(store, profiler):
    store.record_start("job", _utc())  # never finished
    p = profiler.profile("job")
    assert p.run_count == 0
