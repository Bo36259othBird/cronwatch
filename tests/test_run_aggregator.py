"""Tests for RunAggregator and aggregate_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_aggregator import RunAggregator, AggregateReport
from cronwatch.aggregate_formatter import format_aggregate


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def aggregator(store):
    return RunAggregator(store)


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _add_run(store, name, exit_code, duration):
    run_id = store.record_start(name, _utc(2024, 1, 1, 10, 0, 0))
    store.record_finish(run_id, _utc(2024, 1, 1, 10, 0, duration), exit_code)
    return run_id


def test_aggregate_empty_returns_report(aggregator):
    report = aggregator.aggregate(["backup"])
    assert isinstance(report, AggregateReport)
    agg = report.by_name("backup")
    assert agg is not None
    assert agg.total_runs == 0


def test_aggregate_counts_runs(store, aggregator):
    _add_run(store, "backup", 0, 5)
    _add_run(store, "backup", 0, 10)
    _add_run(store, "backup", 1, 3)
    report = aggregator.aggregate(["backup"])
    agg = report.by_name("backup")
    assert agg.total_runs == 3
    assert agg.successful_runs == 2
    assert agg.failed_runs == 1


def test_aggregate_success_rate(store, aggregator):
    _add_run(store, "sync", 0, 2)
    _add_run(store, "sync", 0, 2)
    report = aggregator.aggregate(["sync"])
    agg = report.by_name("sync")
    assert agg.success_rate == 1.0


def test_aggregate_durations(store, aggregator):
    _add_run(store, "job", 0, 4)
    _add_run(store, "job", 0, 8)
    report = aggregator.aggregate(["job"])
    agg = report.by_name("job")
    assert agg.min_duration_seconds == pytest.approx(4.0, abs=0.1)
    assert agg.max_duration_seconds == pytest.approx(8.0, abs=0.1)
    assert agg.avg_duration_seconds == pytest.approx(6.0, abs=0.1)


def test_aggregate_multiple_jobs(store, aggregator):
    _add_run(store, "alpha", 0, 1)
    _add_run(store, "beta", 1, 2)
    report = aggregator.aggregate(["alpha", "beta"])
    assert report.total_jobs == 2
    assert report.total_runs == 2
    assert report.total_failures == 1


def test_format_text_contains_job_name(store, aggregator):
    _add_run(store, "nightly", 0, 5)
    report = aggregator.aggregate(["nightly"])
    output = format_aggregate(report, fmt="text")
    assert "nightly" in output
    assert "Runs" in output


def test_format_json_is_valid(store, aggregator):
    _add_run(store, "weekly", 0, 10)
    report = aggregator.aggregate(["weekly"])
    output = format_aggregate(report, fmt="json")
    data = json.loads(output)
    assert "aggregates" in data
    assert data["total_jobs"] == 1


def test_format_json_success_rate(store, aggregator):
    _add_run(store, "daily", 0, 3)
    _add_run(store, "daily", 1, 3)
    report = aggregator.aggregate(["daily"])
    data = json.loads(format_aggregate(report, fmt="json"))
    agg = data["aggregates"][0]
    assert agg["success_rate"] == pytest.approx(0.5, abs=0.01)
