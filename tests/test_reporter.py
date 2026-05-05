"""Tests for Reporter and JobSummary."""

from datetime import datetime, timedelta

import pytest

from cronwatch.reporter import Reporter, JobSummary
from cronwatch.store import JobStore


@pytest.fixture
def store():
    return JobStore()  # in-memory


@pytest.fixture
def reporter(store):
    return Reporter(store)


def _add_run(store: JobStore, name: str, exit_code: int, offset_seconds: int = 0):
    run_id = store.record_start(name)
    store.record_finish(run_id, exit_code)
    return run_id


def test_generate_returns_report(reporter):
    report = reporter.generate([], period_hours=24)
    assert report.period_hours == 24
    assert isinstance(report.generated_at, datetime)
    assert report.summaries == []


def test_summary_no_runs(reporter):
    report = reporter.generate(["backup"], period_hours=24)
    s = report.summaries[0]
    assert s.job_name == "backup"
    assert s.total_runs == 0
    assert s.successful_runs == 0
    assert s.failed_runs == 0
    assert s.avg_duration_seconds is None
    assert s.last_run_at is None


def test_summary_counts_success_and_failure(store, reporter):
    _add_run(store, "sync", exit_code=0)
    _add_run(store, "sync", exit_code=0)
    _add_run(store, "sync", exit_code=1)
    report = reporter.generate(["sync"], period_hours=24)
    s = report.summaries[0]
    assert s.total_runs == 3
    assert s.successful_runs == 2
    assert s.failed_runs == 1


def test_success_rate(store, reporter):
    _add_run(store, "job", exit_code=0)
    _add_run(store, "job", exit_code=1)
    report = reporter.generate(["job"], period_hours=24)
    assert report.summaries[0].success_rate == 50.0


def test_total_failures_aggregates(store, reporter):
    _add_run(store, "a", exit_code=1)
    _add_run(store, "b", exit_code=1)
    report = reporter.generate(["a", "b"], period_hours=24)
    assert report.total_failures == 2


def test_avg_duration_is_non_negative(store, reporter):
    _add_run(store, "etl", exit_code=0)
    report = reporter.generate(["etl"], period_hours=24)
    avg = report.summaries[0].avg_duration_seconds
    assert avg is not None
    assert avg >= 0.0
