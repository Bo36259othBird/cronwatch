"""Tests for RunSentinel and sentinel_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from cronwatch.store import JobStore
from cronwatch.run_sentinel import RunSentinel, SentinelAlert
from cronwatch.sentinel_formatter import format_sentinel


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def sentinel(store):
    return RunSentinel(store)


UTC = timezone.utc
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _add_run(store, job_name, started_at, success=True):
    run_id = store.record_start(job_name, started_at)
    ended_at = started_at + timedelta(seconds=10)
    store.record_finish(run_id, ended_at, exit_code=0 if success else 1)
    return run_id


def test_check_no_runs_returns_alert(sentinel, store):
    with patch("cronwatch.run_sentinel._utcnow", return_value=_NOW):
        alert = sentinel.check("backup", 3600)
    assert alert is not None
    assert alert.job_name == "backup"
    assert alert.is_never_run is True
    assert alert.overdue_by_seconds == 3600


def test_check_recent_run_returns_none(sentinel, store):
    started_at = _NOW - timedelta(seconds=100)
    _add_run(store, "backup", started_at)
    with patch("cronwatch.run_sentinel._utcnow", return_value=_NOW):
        alert = sentinel.check("backup", 3600)
    assert alert is None


def test_check_overdue_run_returns_alert(sentinel, store):
    started_at = _NOW - timedelta(seconds=7200)
    _add_run(store, "backup", started_at)
    with patch("cronwatch.run_sentinel._utcnow", return_value=_NOW):
        alert = sentinel.check("backup", 3600)
    assert alert is not None
    assert alert.overdue_by_seconds == pytest.approx(3600, abs=2)
    assert alert.is_never_run is False


def test_check_invalid_interval_raises(sentinel):
    with pytest.raises(ValueError):
        sentinel.check("backup", 0)


def test_check_all_returns_only_overdue(sentinel, store):
    _add_run(store, "fresh", _NOW - timedelta(seconds=60))
    # "stale" has no runs
    with patch("cronwatch.run_sentinel._utcnow", return_value=_NOW):
        alerts = sentinel.check_all({"fresh": 3600, "stale": 600})
    assert len(alerts) == 1
    assert alerts[0].job_name == "stale"


def test_text_format_no_alerts():
    out = format_sentinel([])
    assert "within expected cadence" in out


def test_text_format_shows_job_name():
    alert = SentinelAlert("nightly", 86400, None, 86400)
    out = format_sentinel([alert])
    assert "nightly" in out
    assert "SENTINEL" in out


def test_json_format_is_valid_json():
    alert = SentinelAlert("nightly", 86400, _NOW - timedelta(hours=25), 3600)
    out = format_sentinel([alert], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["job_name"] == "nightly"


def test_json_format_never_run_flag():
    alert = SentinelAlert("nightly", 86400, None, 86400)
    out = format_sentinel([alert], fmt="json")
    data = json.loads(out)
    assert data[0]["never_run"] is True
