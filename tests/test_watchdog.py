"""Tests for cronwatch.watchdog."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.watchdog import Watchdog, OverdueRun
from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.store import JobRun


def _make_config(max_duration: int | None = 60) -> CronwatchConfig:
    job = JobConfig(
        name="backup",
        schedule="0 2 * * *",
        max_duration_seconds=max_duration,
    )
    return CronwatchConfig(jobs=[job], db_path=":memory:")


def _make_run(run_id: int, started_at: datetime, finished_at=None) -> JobRun:
    run = MagicMock(spec=JobRun)
    run.run_id = run_id
    run.started_at = started_at
    run.finished_at = finished_at
    return run


@pytest.fixture
def store():
    return MagicMock()


def test_overdue_returns_empty_when_no_runs(store):
    store.get_last_run.return_value = None
    wd = Watchdog(_make_config(), store)
    assert wd.overdue_runs() == []


def test_overdue_returns_empty_when_run_completed(store):
    now = datetime.now(timezone.utc)
    run = _make_run(1, now - timedelta(seconds=120), finished_at=now)
    store.get_last_run.return_value = run
    wd = Watchdog(_make_config(max_duration=60), store)
    assert wd.overdue_runs() == []


def test_overdue_returns_empty_when_within_duration(store):
    now = datetime.now(timezone.utc)
    run = _make_run(1, now - timedelta(seconds=30), finished_at=None)
    store.get_last_run.return_value = run
    wd = Watchdog(_make_config(max_duration=60), store)
    assert wd.overdue_runs() == []


def test_overdue_detects_long_running_job(store):
    now = datetime.now(timezone.utc)
    run = _make_run(42, now - timedelta(seconds=120), finished_at=None)
    store.get_last_run.return_value = run
    wd = Watchdog(_make_config(max_duration=60), store)
    result = wd.overdue_runs()
    assert len(result) == 1
    assert isinstance(result[0], OverdueRun)
    assert result[0].job_name == "backup"
    assert result[0].run_id == 42
    assert result[0].max_duration_seconds == 60
    assert result[0].elapsed_seconds >= 120


def test_no_max_duration_skips_job(store):
    now = datetime.now(timezone.utc)
    run = _make_run(1, now - timedelta(seconds=9999), finished_at=None)
    store.get_last_run.return_value = run
    wd = Watchdog(_make_config(max_duration=None), store)
    assert wd.overdue_runs() == []


def test_new_overdue_runs_deduplicates(store):
    now = datetime.now(timezone.utc)
    run = _make_run(7, now - timedelta(seconds=200), finished_at=None)
    store.get_last_run.return_value = run
    wd = Watchdog(_make_config(max_duration=60), store)
    first = wd.new_overdue_runs()
    second = wd.new_overdue_runs()
    assert len(first) == 1
    assert len(second) == 0


def test_clear_alerted_allows_re_alert(store):
    now = datetime.now(timezone.utc)
    run = _make_run(7, now - timedelta(seconds=200), finished_at=None)
    store.get_last_run.return_value = run
    wd = Watchdog(_make_config(max_duration=60), store)
    wd.new_overdue_runs()
    wd.clear_alerted(7)
    result = wd.new_overdue_runs()
    assert len(result) == 1
