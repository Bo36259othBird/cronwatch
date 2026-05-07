"""Tests for RunStreaker."""
import pytest

from cronwatch.store import JobStore
from cronwatch.run_streaker import RunStreaker, Streak


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def streaker(store):
    return RunStreaker(store)


def _add_run(store, job, exit_code):
    run_id = store.record_start(job)
    store.record_finish(run_id, exit_code)
    return run_id


def test_current_streak_no_runs_returns_none(streaker):
    assert streaker.current_streak("backup") is None


def test_current_streak_single_success(store, streaker):
    _add_run(store, "backup", 0)
    streak = streaker.current_streak("backup")
    assert streak is not None
    assert streak.kind == "success"
    assert streak.length == 1
    assert streak.is_active is True


def test_current_streak_single_failure(store, streaker):
    _add_run(store, "backup", 1)
    streak = streaker.current_streak("backup")
    assert streak.kind == "failure"
    assert streak.length == 1


def test_current_streak_counts_consecutive(store, streaker):
    for _ in range(3):
        _add_run(store, "backup", 1)
    streak = streaker.current_streak("backup")
    assert streak.kind == "failure"
    assert streak.length == 3


def test_current_streak_stops_at_different_kind(store, streaker):
    _add_run(store, "backup", 0)   # oldest
    _add_run(store, "backup", 0)
    _add_run(store, "backup", 1)   # newest
    streak = streaker.current_streak("backup")
    assert streak.kind == "failure"
    assert streak.length == 1


def test_is_concerning_requires_two_failures(store, streaker):
    _add_run(store, "backup", 1)
    streak = streaker.current_streak("backup")
    assert not streak.is_concerning

    _add_run(store, "backup", 1)
    streak = streaker.current_streak("backup")
    assert streak.is_concerning


def test_longest_failure_streak_empty(streaker):
    assert streaker.longest_failure_streak("backup") == 0


def test_longest_failure_streak(store, streaker):
    _add_run(store, "backup", 1)
    _add_run(store, "backup", 1)
    _add_run(store, "backup", 0)
    _add_run(store, "backup", 1)
    assert streaker.longest_failure_streak("backup") == 2
