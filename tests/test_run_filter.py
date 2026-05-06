"""Tests for cronwatch.run_filter."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_filter import RunFilter, RunQuery


@pytest.fixture()
def store(tmp_path):
    s = JobStore(str(tmp_path / "test.db"))
    return s


def _dt(hour: int) -> datetime:
    return datetime(2024, 1, 1, hour, 0, 0, tzinfo=timezone.utc)


def _add(store: JobStore, name: str, hour: int, exit_code: int | None = 0):
    run_id = store.record_start(name, _dt(hour))
    if exit_code is not None:
        store.record_finish(run_id, exit_code, _dt(hour))
    return run_id


@pytest.fixture()
def populated(store):
    _add(store, "backup", 1, exit_code=0)
    _add(store, "backup", 2, exit_code=1)
    _add(store, "backup", 3, exit_code=0)
    _add(store, "cleanup", 4, exit_code=0)
    return store


def test_no_filter_returns_all_runs_for_job(populated):
    q = RunQuery(populated)
    results = q.query(RunFilter(job_name="backup"))
    assert len(results) == 3


def test_since_filters_early_runs(populated):
    q = RunQuery(populated)
    results = q.query(RunFilter(job_name="backup", since=_dt(2)))
    assert all(r.started_at >= _dt(2) for r in results)
    assert len(results) == 2


def test_until_filters_late_runs(populated):
    q = RunQuery(populated)
    results = q.query(RunFilter(job_name="backup", until=_dt(2)))
    assert len(results) == 2


def test_success_only(populated):
    q = RunQuery(populated)
    results = q.query(RunFilter(job_name="backup", success_only=True))
    assert all(r.exit_code == 0 for r in results)
    assert len(results) == 2


def test_failure_only(populated):
    q = RunQuery(populated)
    results = q.query(RunFilter(job_name="backup", failure_only=True))
    assert all(r.exit_code != 0 for r in results)
    assert len(results) == 1


def test_limit_caps_results(populated):
    q = RunQuery(populated)
    results = q.query(RunFilter(job_name="backup", limit=2))
    assert len(results) == 2


def test_mutually_exclusive_flags_raise(populated):
    q = RunQuery(populated)
    with pytest.raises(ValueError):
        q.query(RunFilter(job_name="backup", success_only=True, failure_only=True))


def test_no_job_name_returns_all(populated):
    q = RunQuery(populated)
    results = q.query(RunFilter())
    assert len(results) == 4
