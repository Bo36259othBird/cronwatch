"""Tests for cronwatch.tracker."""

import pytest

from cronwatch.store import JobStore
from cronwatch.tracker import JobTracker


@pytest.fixture
def tracker(tmp_path):
    store = JobStore(db_path=str(tmp_path / "tracker_test.db"))
    return JobTracker(store=store)


def test_start_returns_run_id(tracker):
    run_id = tracker.start("backup")
    assert isinstance(run_id, int)


def test_is_active_after_start(tracker):
    tracker.start("backup")
    assert tracker.is_active("backup") is True


def test_is_not_active_before_start(tracker):
    assert tracker.is_active("backup") is False


def test_finish_clears_active(tracker):
    tracker.start("backup")
    tracker.finish("backup", exit_code=0)
    assert tracker.is_active("backup") is False


def test_finish_returns_job_run(tracker):
    tracker.start("cleanup")
    run = tracker.finish("cleanup", exit_code=0)
    assert run is not None
    assert run.job_name == "cleanup"
    assert run.success is True


def test_finish_unknown_job_returns_none(tracker):
    result = tracker.finish("ghost", exit_code=0)
    assert result is None


def test_active_jobs_list(tracker):
    tracker.start("job_a")
    tracker.start("job_b")
    active = tracker.active_jobs()
    assert set(active) == {"job_a", "job_b"}


def test_last_run_after_finish(tracker):
    tracker.start("report")
    tracker.finish("report", exit_code=2)
    run = tracker.last_run("report")
    assert run is not None
    assert run.exit_code == 2
    assert run.success is False
