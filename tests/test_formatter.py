"""Tests for the report formatter."""

import json
from datetime import datetime

import pytest

from cronwatch.formatter import format_report
from cronwatch.reporter import JobSummary, Report


def _make_report(failures: int = 1) -> Report:
    summaries = [
        JobSummary(
            job_name="daily-backup",
            total_runs=10,
            successful_runs=10 - failures,
            failed_runs=failures,
            avg_duration_seconds=42.5,
            last_run_at=datetime(2024, 1, 15, 6, 0, 0),
            last_exit_code=0 if failures == 0 else 1,
        )
    ]
    return Report(
        generated_at=datetime(2024, 1, 15, 8, 0, 0),
        period_hours=24,
        summaries=summaries,
    )


def test_text_format_contains_job_name():
    text = format_report(_make_report(), fmt="text")
    assert "daily-backup" in text


def test_text_format_contains_header():
    text = format_report(_make_report(), fmt="text")
    assert "CronWatch Report" in text


def test_text_format_shows_failure_count():
    text = format_report(_make_report(failures=3), fmt="text")
    assert "Total failures: 3" in text


def test_json_format_is_valid_json():
    output = format_report(_make_report(), fmt="json")
    data = json.loads(output)  # must not raise
    assert "jobs" in data


def test_json_format_job_fields():
    output = format_report(_make_report(), fmt="json")
    job = json.loads(output)["jobs"][0]
    assert job["job_name"] == "daily-backup"
    assert job["total_runs"] == 10
    assert job["avg_duration_seconds"] == 42.5


def test_json_format_success_rate():
    output = format_report(_make_report(failures=2), fmt="json")
    job = json.loads(output)["jobs"][0]
    assert job["success_rate"] == 80.0


def test_invalid_format_raises():
    with pytest.raises((ValueError, TypeError, KeyError)):
        format_report(_make_report(), fmt="csv")  # type: ignore
