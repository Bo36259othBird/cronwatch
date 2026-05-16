"""Tests for escalation_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.run_escalator import EscalationLevel
from cronwatch.escalation_formatter import format_escalation


def _utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def warning_level():
    return EscalationLevel(
        job_name="backup",
        level=1,
        consecutive_failures=3,
        first_failure_at=_utc(2024, 1, 1, 6, 0),
        last_failure_at=_utc(2024, 1, 1, 8, 0),
    )


@pytest.fixture()
def normal_level():
    return EscalationLevel(
        job_name="healthcheck",
        level=0,
        consecutive_failures=0,
        first_failure_at=None,
        last_failure_at=None,
    )


def test_text_contains_header(warning_level):
    out = format_escalation([warning_level])
    assert "Escalation Report" in out


def test_text_contains_job_name(warning_level):
    out = format_escalation([warning_level])
    assert "backup" in out


def test_text_shows_warning_label(warning_level):
    out = format_escalation([warning_level])
    assert "warning" in out


def test_text_shows_normal_ok_indicator(normal_level):
    out = format_escalation([normal_level])
    assert "[ok]" in out


def test_text_shows_critical_indicator():
    lvl = EscalationLevel(
        job_name="deploy",
        level=2,
        consecutive_failures=6,
        first_failure_at=_utc(2024, 1, 2, 0, 0),
        last_failure_at=_utc(2024, 1, 2, 5, 0),
    )
    out = format_escalation([lvl])
    assert "[!!]" in out
    assert "critical" in out


def test_text_empty_list():
    out = format_escalation([])
    assert "No escalation data" in out


def test_json_format_is_valid(warning_level):
    out = format_escalation([warning_level], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["job"] == "backup"


def test_json_contains_level_fields(warning_level):
    out = format_escalation([warning_level], fmt="json")
    data = json.loads(out)
    record = data[0]
    assert "level" in record
    assert "label" in record
    assert "consecutive_failures" in record
