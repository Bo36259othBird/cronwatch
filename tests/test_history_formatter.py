"""Tests for cronwatch.history_formatter."""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from cronwatch.history import JobTrend
from cronwatch.history_formatter import format_trends


def _trend(name="backup", total=10, ok=8, fail=2, avg=30.0, degrading=False):
    return JobTrend(
        job_name=name,
        window_days=7,
        total_runs=total,
        successful_runs=ok,
        failed_runs=fail,
        avg_duration_seconds=avg,
        last_run_at=datetime(2024, 1, 15, 12, 0, 0),
    )


def test_text_contains_job_name():
    out = format_trends([_trend("nightly")])
    assert "nightly" in out


def test_text_contains_counts():
    out = format_trends([_trend(total=10, ok=8, fail=2)])
    assert "runs=10" in out
    assert "ok=8" in out
    assert "fail=2" in out


def test_text_shows_degrading_flag():
    t = _trend(total=4, ok=1, fail=3)
    out = format_trends([t])
    assert "DEGRADING" in out


def test_text_no_degrading_flag_when_healthy():
    t = _trend(total=10, ok=10, fail=0)
    out = format_trends([t])
    assert "DEGRADING" not in out


def test_text_empty_list():
    out = format_trends([])
    assert "No trend data" in out


def test_json_is_valid():
    out = format_trends([_trend()], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1


def test_json_fields_present():
    out = format_trends([_trend("sync")], fmt="json")
    data = json.loads(out)
    record = data[0]
    assert record["job_name"] == "sync"
    assert "failure_rate" in record
    assert "avg_duration_seconds" in record
    assert "is_degrading" in record


def test_json_multiple_trends():
    trends = [_trend("a"), _trend("b"), _trend("c")]
    out = format_trends(trends, fmt="json")
    data = json.loads(out)
    assert len(data) == 3
