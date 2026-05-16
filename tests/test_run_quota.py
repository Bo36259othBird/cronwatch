"""Tests for RunQuotaChecker and quota_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_quota import QuotaResult, RunQuotaChecker, is_exceeded
from cronwatch.quota_formatter import format_quota


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def checker(store):
    return RunQuotaChecker(store)


def _utc(year=2024, month=1, day=1, hour=12, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def _add_run(store, job_name, started_at, exit_code=0):
    run_id = store.record_start(job_name, started_at)
    store.record_finish(run_id, started_at, exit_code)
    return run_id


# --- RunQuotaChecker ---------------------------------------------------------

def test_check_no_runs_returns_zero_actual(checker):
    ref = _utc()
    result = checker.check("nightly", limit=5, window_seconds=3600, reference=ref)
    assert result.actual == 0
    assert not result.exceeded
    assert result.excess == 0


def test_check_returns_quota_result_instance(checker):
    ref = _utc()
    result = checker.check("nightly", limit=5, window_seconds=3600, reference=ref)
    assert isinstance(result, QuotaResult)


def test_check_counts_runs_within_window(store, checker):
    ref = _utc(hour=13)
    for minute in range(3):
        _add_run(store, "nightly", _utc(hour=12, minute=minute * 10))
    result = checker.check("nightly", limit=5, window_seconds=7200, reference=ref)
    assert result.actual == 3
    assert not result.exceeded


def test_check_excludes_runs_outside_window(store, checker):
    ref = _utc(hour=13)
    _add_run(store, "nightly", _utc(hour=10))  # outside 1-hour window
    _add_run(store, "nightly", _utc(hour=12, minute=30))  # inside
    result = checker.check("nightly", limit=5, window_seconds=3600, reference=ref)
    assert result.actual == 1


def test_check_detects_exceeded_quota(store, checker):
    ref = _utc(hour=13)
    for minute in range(4):
        _add_run(store, "nightly", _utc(hour=12, minute=minute * 5))
    result = checker.check("nightly", limit=2, window_seconds=7200, reference=ref)
    assert result.exceeded
    assert result.excess == 2


def test_utilisation_within_limit(store, checker):
    ref = _utc(hour=13)
    _add_run(store, "nightly", _utc(hour=12, minute=30))
    result = checker.check("nightly", limit=4, window_seconds=3600, reference=ref)
    assert abs(result.utilisation - 0.25) < 0.001


def test_is_exceeded_helper():
    r = QuotaResult("j", 3600, 3, 5, True, 2)
    assert is_exceeded(r)
    r2 = QuotaResult("j", 3600, 3, 2, False, 0)
    assert not is_exceeded(r2)


# --- format_quota ------------------------------------------------------------

def test_text_format_contains_job_name(store, checker):
    ref = _utc(hour=13)
    _add_run(store, "nightly", _utc(hour=12, minute=30))
    result = checker.check("nightly", limit=5, window_seconds=3600, reference=ref)
    output = format_quota([result], fmt="text")
    assert "nightly" in output


def test_text_format_shows_exceeded(store, checker):
    ref = _utc(hour=13)
    for m in range(4):
        _add_run(store, "nightly", _utc(hour=12, minute=m * 5))
    result = checker.check("nightly", limit=2, window_seconds=7200, reference=ref)
    output = format_quota([result], fmt="text")
    assert "EXCEEDED" in output


def test_text_format_empty_returns_message():
    output = format_quota([], fmt="text")
    assert "No quota" in output


def test_json_format_is_valid_json(store, checker):
    ref = _utc(hour=13)
    _add_run(store, "nightly", _utc(hour=12, minute=30))
    result = checker.check("nightly", limit=5, window_seconds=3600, reference=ref)
    output = format_quota([result], fmt="json")
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["job_name"] == "nightly"


def test_json_format_contains_utilisation(store, checker):
    ref = _utc(hour=13)
    _add_run(store, "nightly", _utc(hour=12, minute=30))
    result = checker.check("nightly", limit=4, window_seconds=3600, reference=ref)
    output = format_quota([result], fmt="json")
    data = json.loads(output)
    assert "utilisation" in data[0]
