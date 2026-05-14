"""Tests for RunThrottler and throttle_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_throttler import RunThrottler, ThrottleViolation
from cronwatch.throttle_formatter import format_throttle


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def throttler(store):
    return RunThrottler(store)


def _add_run(store, job_name, started_at, finished_at=None, exit_code=0):
    run_id = store.record_start(job_name, started_at)
    if finished_at is not None:
        store.record_finish(run_id, finished_at, exit_code)
    return run_id


def test_check_no_runs_returns_empty(store, throttler):
    result = throttler.check("backup", min_gap_seconds=300)
    assert result == []


def test_check_single_run_returns_empty(store, throttler):
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 0))
    result = throttler.check("backup", min_gap_seconds=300)
    assert result == []


def test_check_detects_violation(store, throttler):
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 0))
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 1))  # only 60s apart
    result = throttler.check("backup", min_gap_seconds=300)
    assert len(result) == 1
    assert result[0].job_name == "backup"
    assert result[0].gap_seconds == pytest.approx(60.0)
    assert result[0].is_violation is True


def test_check_no_violation_when_gap_sufficient(store, throttler):
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 0))
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 10))  # 600s apart
    result = throttler.check("backup", min_gap_seconds=300)
    assert result == []


def test_check_multiple_violations(store, throttler):
    _add_run(store, "sync", _utc(2024, 1, 1, 3, 0))
    _add_run(store, "sync", _utc(2024, 1, 1, 3, 1))
    _add_run(store, "sync", _utc(2024, 1, 1, 3, 2))
    result = throttler.check("sync", min_gap_seconds=300)
    assert len(result) == 2


def test_any_violations_true(store, throttler):
    _add_run(store, "job", _utc(2024, 1, 1, 0, 0))
    _add_run(store, "job", _utc(2024, 1, 1, 0, 1))
    assert throttler.any_violations("job", min_gap_seconds=120) is True


def test_any_violations_false(store, throttler):
    _add_run(store, "job", _utc(2024, 1, 1, 0, 0))
    _add_run(store, "job", _utc(2024, 1, 1, 1, 0))
    assert throttler.any_violations("job", min_gap_seconds=120) is False


def test_format_text_no_violations():
    out = format_throttle([], fmt="text")
    assert "No throttle violations" in out


def test_format_text_with_violation(store, throttler):
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 0))
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 1))
    violations = throttler.check("backup", min_gap_seconds=300)
    out = format_throttle(violations, fmt="text")
    assert "backup" in out
    assert "violation" in out.lower()


def test_format_json_returns_valid_json(store, throttler):
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 0))
    _add_run(store, "backup", _utc(2024, 1, 1, 2, 1))
    violations = throttler.check("backup", min_gap_seconds=300)
    out = format_throttle(violations, fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["job_name"] == "backup"
    assert data[0]["is_violation"] is True
