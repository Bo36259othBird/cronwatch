"""Tests for cronwatch.run_cooldown."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from cronwatch.store import JobStore
from cronwatch.run_cooldown import CooldownStatus, RunCooldownChecker


UTC = timezone.utc
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def checker(store):
    return RunCooldownChecker(store)


def _add_run(store, job_name, finished_at, success=True):
    run_id = store.record_start(job_name, datetime(2024, 6, 1, 11, 0, 0, tzinfo=UTC))
    store.record_finish(run_id, finished_at, success)
    return run_id


def test_check_no_runs_returns_not_in_cooldown(checker):
    status = checker.check("backup", 300)
    assert isinstance(status, CooldownStatus)
    assert status.in_cooldown is False
    assert status.remaining_seconds == 0.0
    assert status.last_finished is None


def test_check_is_ready_when_no_runs(checker):
    status = checker.check("backup", 300)
    assert status.is_ready() is True


def test_check_in_cooldown_when_recently_finished(store, checker):
    finished = _NOW - timedelta(seconds=60)
    _add_run(store, "backup", finished)

    with patch("cronwatch.run_cooldown._utcnow", return_value=_NOW):
        status = checker.check("backup", 300)

    assert status.in_cooldown is True
    assert status.remaining_seconds == pytest.approx(240.0)
    assert status.is_ready() is False


def test_check_not_in_cooldown_when_cooldown_expired(store, checker):
    finished = _NOW - timedelta(seconds=400)
    _add_run(store, "backup", finished)

    with patch("cronwatch.run_cooldown._utcnow", return_value=_NOW):
        status = checker.check("backup", 300)

    assert status.in_cooldown is False
    assert status.remaining_seconds == 0.0
    assert status.is_ready() is True


def test_check_remaining_never_negative(store, checker):
    finished = _NOW - timedelta(seconds=9999)
    _add_run(store, "backup", finished)

    with patch("cronwatch.run_cooldown._utcnow", return_value=_NOW):
        status = checker.check("backup", 300)

    assert status.remaining_seconds >= 0.0


def test_check_all_returns_status_for_each_job(store, checker):
    finished = _NOW - timedelta(seconds=60)
    _add_run(store, "alpha", finished)
    _add_run(store, "beta", finished)

    with patch("cronwatch.run_cooldown._utcnow", return_value=_NOW):
        results = checker.check_all({"alpha": 300, "beta": 30})

    assert len(results) == 2
    names = {r.job_name for r in results}
    assert names == {"alpha", "beta"}


def test_check_all_respects_per_job_cooldown(store, checker):
    finished = _NOW - timedelta(seconds=60)
    _add_run(store, "alpha", finished)
    _add_run(store, "beta", finished)

    with patch("cronwatch.run_cooldown._utcnow", return_value=_NOW):
        results = checker.check_all({"alpha": 300, "beta": 30})

    by_name = {r.job_name: r for r in results}
    assert by_name["alpha"].in_cooldown is True
    assert by_name["beta"].in_cooldown is False
