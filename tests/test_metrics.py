"""Tests for MetricsCollector and metrics_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.metrics import MetricsCollector
from cronwatch.metrics_formatter import format_metrics


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def collector(store):
    return MetricsCollector(store)


def _add_run(store: JobStore, name: str, exit_code: int, duration: float) -> None:
    t0 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    from datetime import timedelta
    t1 = t0 + timedelta(seconds=duration)
    run_id = store.record_start(name, t0)
    store.record_finish(run_id, exit_code, t1)


def test_collect_returns_metrics_for_known_job(store, collector):
    _add_run(store, "backup", 0, 10.0)
    report = collector.collect(["backup"])
    assert report.by_name("backup") is not None


def test_collect_counts_runs(store, collector):
    _add_run(store, "backup", 0, 5.0)
    _add_run(store, "backup", 0, 7.0)
    _add_run(store, "backup", 1, 2.0)
    m = collector.collect(["backup"]).by_name("backup")
    assert m.total_runs == 3
    assert m.successful_runs == 2
    assert m.failed_runs == 1


def test_success_rate_all_pass(store, collector):
    _add_run(store, "sync", 0, 3.0)
    _add_run(store, "sync", 0, 4.0)
    m = collector.collect(["sync"]).by_name("sync")
    assert m.success_rate == pytest.approx(1.0)


def test_success_rate_no_runs(store, collector):
    m = collector.collect(["ghost"]).by_name("ghost")
    assert m.success_rate == pytest.approx(0.0)
    assert m.avg_duration_seconds is None


def test_duration_stats(store, collector):
    _add_run(store, "etl", 0, 10.0)
    _add_run(store, "etl", 0, 20.0)
    m = collector.collect(["etl"]).by_name("etl")
    assert m.min_duration_seconds == pytest.approx(10.0)
    assert m.max_duration_seconds == pytest.approx(20.0)
    assert m.avg_duration_seconds == pytest.approx(15.0)


def test_text_format_contains_job_name(store, collector):
    _add_run(store, "cleanup", 0, 1.0)
    report = collector.collect(["cleanup"])
    text = format_metrics(report, fmt="text")
    assert "cleanup" in text


def test_text_format_shows_success_percent(store, collector):
    _add_run(store, "cleanup", 0, 1.0)
    report = collector.collect(["cleanup"])
    text = format_metrics(report, fmt="text")
    assert "100.0%" in text


def test_json_format_is_valid(store, collector):
    _add_run(store, "index", 1, 3.0)
    report = collector.collect(["index"])
    raw = format_metrics(report, fmt="json")
    data = json.loads(raw)
    assert "metrics" in data
    assert data["metrics"][0]["job_name"] == "index"
