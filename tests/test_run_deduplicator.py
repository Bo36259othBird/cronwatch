"""Tests for RunDeduplicator."""

from datetime import datetime, timezone, timedelta

import pytest

from cronwatch.store import JobStore
from cronwatch.run_deduplicator import RunDeduplicator, DuplicateGroup


@pytest.fixture
def store(tmp_path):
    db = str(tmp_path / "test.db")
    return JobStore(db)


@pytest.fixture
def deduplicator(store):
    return RunDeduplicator(store, window_seconds=60)


def _utc(offset_seconds: int = 0) -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


def _add_run(store, job_name, started_at, exit_code=0):
    run_id = store.record_start(job_name, started_at)
    store.record_finish(run_id, started_at + timedelta(seconds=5), exit_code)
    return run_id


def test_no_runs_returns_empty(store, deduplicator):
    result = deduplicator.find_duplicates("backup")
    assert result == []


def test_single_run_no_duplicates(store, deduplicator):
    _add_run(store, "backup", _utc(0))
    result = deduplicator.find_duplicates("backup")
    assert result == []


def test_two_runs_within_window_are_duplicates(store, deduplicator):
    _add_run(store, "backup", _utc(0))
    _add_run(store, "backup", _utc(30))
    groups = deduplicator.find_duplicates("backup")
    assert len(groups) == 1
    assert groups[0].count == 2
    assert groups[0].is_duplicate is True


def test_two_runs_outside_window_not_duplicates(store, deduplicator):
    _add_run(store, "backup", _utc(0))
    _add_run(store, "backup", _utc(120))
    result = deduplicator.find_duplicates("backup")
    assert result == []


def test_three_runs_all_within_window(store, deduplicator):
    _add_run(store, "backup", _utc(0))
    _add_run(store, "backup", _utc(10))
    _add_run(store, "backup", _utc(20))
    groups = deduplicator.find_duplicates("backup")
    assert len(groups) == 1
    assert groups[0].count == 3


def test_duplicate_group_has_correct_job_name(store, deduplicator):
    _add_run(store, "sync", _utc(0))
    _add_run(store, "sync", _utc(5))
    groups = deduplicator.find_duplicates("sync")
    assert groups[0].job_name == "sync"


def test_has_duplicates_returns_true_when_dupes_exist(store, deduplicator):
    _add_run(store, "cleanup", _utc(0))
    _add_run(store, "cleanup", _utc(15))
    assert deduplicator.has_duplicates("cleanup") is True


def test_has_duplicates_returns_false_when_no_dupes(store, deduplicator):
    _add_run(store, "cleanup", _utc(0))
    assert deduplicator.has_duplicates("cleanup") is False


def test_different_jobs_do_not_interfere(store, deduplicator):
    _add_run(store, "job_a", _utc(0))
    _add_run(store, "job_a", _utc(10))
    _add_run(store, "job_b", _utc(0))
    assert deduplicator.has_duplicates("job_a") is True
    assert deduplicator.has_duplicates("job_b") is False
