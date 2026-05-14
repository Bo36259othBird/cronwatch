"""Tests for run_budget and budget_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

import pytest

from cronwatch.store import JobStore
from cronwatch.run_budget import RunBudgetChecker, BudgetResult
from cronwatch.budget_formatter import format_budget


def _utc(offset_seconds: float = 0) -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def checker(store):
    return RunBudgetChecker(store)


def _add_run(
    store: JobStore,
    job_name: str,
    duration_seconds: float,
    success: bool = True,
) -> int:
    run_id = store.record_start(job_name, _utc())
    store.record_finish(run_id, _utc(duration_seconds), 0 if success else 1)
    return run_id


def test_check_no_runs_returns_none(checker):
    assert checker.check("backup", 60.0) is None


def test_check_within_budget(store, checker):
    _add_run(store, "backup", 30.0)
    result = checker.check("backup", 60.0)
    assert isinstance(result, BudgetResult)
    assert result.exceeded is False
    assert result.overage_seconds is None
    assert result.actual_seconds == pytest.approx(30.0)


def test_check_exceeds_budget(store, checker):
    _add_run(store, "backup", 90.0)
    result = checker.check("backup", 60.0)
    assert result.exceeded is True
    assert result.overage_seconds == pytest.approx(30.0)


def test_within_budget_property(store, checker):
    _add_run(store, "sync", 10.0)
    result = checker.check("sync", 20.0)
    assert result.within_budget is True


def test_check_all_skips_missing_jobs(store, checker):
    _add_run(store, "job_a", 5.0)
    results = checker.check_all({"job_a": 10.0, "job_b": 10.0})
    assert len(results) == 1
    assert results[0].job_name == "job_a"


def test_check_all_returns_all_results(store, checker):
    _add_run(store, "job_a", 5.0)
    _add_run(store, "job_b", 20.0)
    results = checker.check_all({"job_a": 10.0, "job_b": 10.0})
    assert len(results) == 2


def test_format_budget_text_contains_job_name(store, checker):
    _add_run(store, "nightly", 45.0)
    results = checker.check_all({"nightly": 60.0})
    output = format_budget(results, fmt="text")
    assert "nightly" in output


def test_format_budget_text_shows_exceeded(store, checker):
    _add_run(store, "heavy", 120.0)
    results = checker.check_all({"heavy": 60.0})
    output = format_budget(results, fmt="text")
    assert "EXCEEDED" in output


def test_format_budget_json_is_valid(store, checker):
    _add_run(store, "quick", 5.0)
    results = checker.check_all({"quick": 30.0})
    output = format_budget(results, fmt="json")
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["job_name"] == "quick"


def test_format_budget_empty_text(checker):
    output = format_budget([], fmt="text")
    assert "No budget results" in output
