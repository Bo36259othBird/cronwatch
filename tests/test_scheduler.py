"""Tests for cronwatch.scheduler.ScheduleChecker."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.config import JobConfig
from cronwatch.scheduler import ScheduleChecker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _job(schedule: str = "*/5 * * * *", silence_threshold: int = 300) -> JobConfig:
    return JobConfig(
        name="test-job",
        schedule=schedule,
        silence_threshold=silence_threshold,
        tags=[],
    )


def _checker(now: datetime) -> ScheduleChecker:
    return ScheduleChecker(now_fn=lambda: now)


# ---------------------------------------------------------------------------
# expected_last_run
# ---------------------------------------------------------------------------

def test_expected_last_run_returns_datetime():
    now = _utc(2024, 1, 15, 12, 7, 0)
    checker = _checker(now)
    result = checker.expected_last_run("*/5 * * * *")
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


def test_expected_last_run_is_before_now():
    now = _utc(2024, 1, 15, 12, 7, 0)
    checker = _checker(now)
    result = checker.expected_last_run("*/5 * * * *")
    assert result < now


def test_expected_last_run_five_minute_schedule():
    # At 12:07, the last 5-minute tick should be 12:05.
    now = _utc(2024, 1, 15, 12, 7, 0)
    checker = _checker(now)
    result = checker.expected_last_run("*/5 * * * *")
    assert result == _utc(2024, 1, 15, 12, 5, 0)


def test_expected_last_run_uses_reference():
    reference = _utc(2024, 1, 15, 12, 10, 0)
    checker = _checker(_utc(2024, 1, 15, 13, 0, 0))  # now is different
    result = checker.expected_last_run("*/5 * * * *", reference=reference)
    assert result == _utc(2024, 1, 15, 12, 10, 0)


# ---------------------------------------------------------------------------
# is_overdue — never ran
# ---------------------------------------------------------------------------

def test_is_overdue_never_ran_within_threshold():
    # Expected tick was 30 s ago; threshold is 300 s → not overdue yet.
    now = _utc(2024, 1, 15, 12, 5, 30)
    checker = _checker(now)
    job = _job(schedule="*/5 * * * *", silence_threshold=300)
    assert checker.is_overdue(job, last_run=None) is False


def test_is_overdue_never_ran_past_threshold():
    # Expected tick was 6 minutes ago; threshold is 300 s → overdue.
    now = _utc(2024, 1, 15, 12, 11, 0)
    checker = _checker(now)
    job = _job(schedule="*/5 * * * *", silence_threshold=300)
    assert checker.is_overdue(job, last_run=None) is True


# ---------------------------------------------------------------------------
# is_overdue — has run before
# ---------------------------------------------------------------------------

def test_is_overdue_ran_after_last_tick():
    now = _utc(2024, 1, 15, 12, 7, 0)
    checker = _checker(now)
    job = _job(schedule="*/5 * * * *")
    last_run = _utc(2024, 1, 15, 12, 5, 10)  # ran after 12:05 tick
    assert checker.is_overdue(job, last_run=last_run) is False


def test_is_overdue_ran_before_last_tick():
    now = _utc(2024, 1, 15, 12, 7, 0)
    checker = _checker(now)
    job = _job(schedule="*/5 * * * *")
    last_run = _utc(2024, 1, 15, 12, 0, 0)  # missed the 12:05 tick
    assert checker.is_overdue(job, last_run=last_run) is True


def test_is_overdue_handles_naive_last_run():
    now = _utc(2024, 1, 15, 12, 7, 0)
    checker = _checker(now)
    job = _job(schedule="*/5 * * * *")
    naive_last_run = datetime(2024, 1, 15, 12, 5, 10)  # no tzinfo
    assert checker.is_overdue(job, last_run=naive_last_run) is False
