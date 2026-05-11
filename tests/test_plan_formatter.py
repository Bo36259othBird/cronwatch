"""Tests for cronwatch.plan_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.plan_formatter import format_plans
from cronwatch.run_planner import RunPlan


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _plan(
    name: str = "backup",
    last_run=None,
    next_expected=None,
    overdue: bool = False,
    secs: float | None = 120.0,
) -> RunPlan:
    return RunPlan(
        job_name=name,
        last_run=last_run,
        next_expected=next_expected,
        is_overdue=overdue,
        seconds_until_due=secs,
    )


# ---------------------------------------------------------------------------
# Text format
# ---------------------------------------------------------------------------

def test_text_contains_header():
    out = format_plans([_plan()], fmt="text")
    assert "Run Planner" in out


def test_text_contains_job_name():
    out = format_plans([_plan(name="nightly")], fmt="text")
    assert "nightly" in out


def test_text_shows_overdue_status():
    out = format_plans([_plan(overdue=True)], fmt="text")
    assert "OVERDUE" in out


def test_text_shows_ok_status_when_not_overdue():
    out = format_plans([_plan(overdue=False)], fmt="text")
    assert "ok" in out


def test_text_shows_na_for_none_dates():
    out = format_plans([_plan()], fmt="text")
    assert "N/A" in out


def test_text_shows_formatted_datetime():
    dt = _utc(2024, 3, 15, 8, 30, 0)
    out = format_plans([_plan(last_run=dt)], fmt="text")
    assert "2024-03-15" in out


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def test_json_format_is_valid_json():
    out = format_plans([_plan()], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)


def test_json_contains_job_name():
    out = format_plans([_plan(name="sync")], fmt="json")
    data = json.loads(out)
    assert data[0]["job_name"] == "sync"


def test_json_overdue_field():
    out = format_plans([_plan(overdue=True)], fmt="json")
    data = json.loads(out)
    assert data[0]["is_overdue"] is True


def test_json_multiple_plans():
    plans = [_plan("a"), _plan("b")]
    out = format_plans(plans, fmt="json")
    data = json.loads(out)
    assert len(data) == 2
