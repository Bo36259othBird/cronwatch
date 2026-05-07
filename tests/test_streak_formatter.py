"""Tests for streak_formatter."""
import json

import pytest

from cronwatch.run_streaker import Streak
from cronwatch.streak_formatter import format_streak, format_streaks


@pytest.fixture()
def failure_streak():
    return Streak(job_name="nightly", kind="failure", length=3, is_active=True)


@pytest.fixture()
def success_streak():
    return Streak(job_name="hourly", kind="success", length=5, is_active=True)


def test_text_contains_job_name(failure_streak):
    out = format_streak(failure_streak, fmt="text")
    assert "nightly" in out


def test_text_shows_kind_and_length(failure_streak):
    out = format_streak(failure_streak, fmt="text")
    assert "FAILURE" in out
    assert "x3" in out


def test_text_flags_concerning_streak(failure_streak):
    out = format_streak(failure_streak, fmt="text")
    assert "[!]" in out


def test_text_no_flag_for_success(success_streak):
    out = format_streak(success_streak, fmt="text")
    assert "[!]" not in out


def test_json_format_is_valid(failure_streak):
    out = format_streak(failure_streak, fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["job"] == "nightly"


def test_json_includes_is_concerning(failure_streak):
    out = format_streak(failure_streak, fmt="json")
    data = json.loads(out)
    assert data[0]["is_concerning"] is True


def test_format_streaks_multiple(failure_streak, success_streak):
    out = format_streaks([failure_streak, success_streak], fmt="text")
    assert "nightly" in out
    assert "hourly" in out


def test_format_streaks_empty():
    out = format_streaks([], fmt="text")
    assert "No streak" in out
