"""Tests for RunSummarizer."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_summarizer import RunSummary, RunSummarizer


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def summarizer(store):
    return RunSummarizer(store)


def _utc(**kwargs):
    return datetime.now(tz=timezone.utc) - timedelta(**kwargs)


def _add_run(store, job_name, *, hours_ago_start=1, duration_s=10, exit_code=0):
    started = _utc(hours=hours_ago_start)
    finished = started + timedelta(seconds=duration_s)
    run_id = store.record_start(job_name, started)
    store.record_finish(run_id, exit_code, finished)
    return run_id


def test_summarize_returns_run_summary_instance(store, summarizer):
    result = summarizer.summarize("backup")
    assert isinstance(result, RunSummary)


def test_summarize_no_runs_returns_zero_counts(store, summarizer):
    result = summarizer.summarize("backup")
    assert result.total_runs == 0
    assert result.successful_runs == 0
    assert result.failed_runs == 0


def test_summarize_no_runs_returns_none_durations(store, summarizer):
    result = summarizer.summarize("backup")
    assert result.avg_duration_seconds is None
    assert result.min_duration_seconds is None
    assert result.max_duration_seconds is None


def test_summarize_counts_successful_runs(store, summarizer):
    _add_run(store, "backup", exit_code=0)
    _add_run(store, "backup", exit_code=0)
    result = summarizer.summarize("backup")
    assert result.total_runs == 2
    assert result.successful_runs == 2
    assert result.failed_runs == 0


def test_summarize_counts_failed_runs(store, summarizer):
    _add_run(store, "backup", exit_code=0)
    _add_run(store, "backup", exit_code=1)
    result = summarizer.summarize("backup")
    assert result.failed_runs == 1
    assert result.successful_runs == 1


def test_success_rate_all_success(store, summarizer):
    _add_run(store, "backup", exit_code=0)
    _add_run(store, "backup", exit_code=0)
    result = summarizer.summarize("backup")
    assert result.success_rate == pytest.approx(1.0)


def test_success_rate_no_runs_is_zero(store, summarizer):
    result = summarizer.summarize("backup")
    assert result.success_rate == 0.0


def test_summarize_computes_avg_duration(store, summarizer):
    _add_run(store, "backup", duration_s=10)
    _add_run(store, "backup", duration_s=20)
    result = summarizer.summarize("backup")
    assert result.avg_duration_seconds == pytest.approx(15.0)


def test_summarize_computes_min_max_duration(store, summarizer):
    _add_run(store, "backup", duration_s=5)
    _add_run(store, "backup", duration_s=30)
    result = summarizer.summarize("backup")
    assert result.min_duration_seconds == pytest.approx(5.0)
    assert result.max_duration_seconds == pytest.approx(30.0)


def test_summarize_excludes_runs_outside_window(store, summarizer):
    _add_run(store, "backup", hours_ago_start=1, exit_code=0)
    _add_run(store, "backup", hours_ago_start=50, exit_code=0)
    result = summarizer.summarize("backup", window_hours=24)
    assert result.total_runs == 1


def test_summarize_stores_window_hours(store, summarizer):
    result = summarizer.summarize("backup", window_hours=48)
    assert result.window_hours == 48


def test_summarize_stores_job_name(store, summarizer):
    result = summarizer.summarize("my_job")
    assert result.job_name == "my_job"
