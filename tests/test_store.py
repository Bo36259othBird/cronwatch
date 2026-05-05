"""Tests for cronwatch.store."""

import time
import pytest

from cronwatch.store import JobStore, JobRun


@pytest.fixture
def store(tmp_path):
    return JobStore(db_path=str(tmp_path / "test.db"))


def test_record_start_returns_int(store):
    run_id = store.record_start("backup")
    assert isinstance(run_id, int)
    assert run_id > 0


def test_get_last_run_none_before_any_run(store):
    assert store.get_last_run("nonexistent") is None


def test_record_start_and_last_run(store):
    store.record_start("backup")
    run = store.get_last_run("backup")
    assert run is not None
    assert run.job_name == "backup"
    assert run.finished_at is None
    assert run.success is None


def test_record_finish_success(store):
    run_id = store.record_start("cleanup")
    time.sleep(0.05)
    store.record_finish(run_id, exit_code=0)
    run = store.get_last_run("cleanup")
    assert run.exit_code == 0
    assert run.success is True
    assert run.duration is not None
    assert run.duration >= 0.05


def test_record_finish_failure(store):
    run_id = store.record_start("report")
    store.record_finish(run_id, exit_code=1)
    run = store.get_last_run("report")
    assert run.success is False
    assert run.exit_code == 1


def test_get_runs_returns_multiple(store):
    for _ in range(3):
        rid = store.record_start("daily")
        store.record_finish(rid, exit_code=0)
    runs = store.get_runs("daily")
    assert len(runs) == 3


def test_get_runs_respects_limit(store):
    for _ in range(10):
        rid = store.record_start("hourly")
        store.record_finish(rid, exit_code=0)
    runs = store.get_runs("hourly", limit=3)
    assert len(runs) == 3


def test_get_runs_empty_for_unknown_job(store):
    assert store.get_runs("ghost") == []
