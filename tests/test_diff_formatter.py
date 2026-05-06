"""Tests for diff_formatter."""
from __future__ import annotations

import json

import pytest

from cronwatch.diff_formatter import format_diff
from cronwatch.run_comparator import RunDiff


def _diff(**kwargs) -> RunDiff:  # type: ignore[no-untyped-def]
    defaults = dict(
        job_name="backup",
        run_id_a=1,
        run_id_b=2,
        duration_a=10.0,
        duration_b=20.0,
        exit_code_a=0,
        exit_code_b=0,
        duration_delta=10.0,
        status_changed=False,
    )
    defaults.update(kwargs)
    return RunDiff(**defaults)


def test_text_contains_job_name() -> None:
    out = format_diff(_diff(), fmt="text")
    assert "backup" in out


def test_text_shows_run_ids() -> None:
    out = format_diff(_diff(), fmt="text")
    assert "id=1" in out
    assert "id=2" in out


def test_text_shows_slower_trend() -> None:
    out = format_diff(_diff(duration_delta=5.0), fmt="text")
    assert "SLOWER" in out


def test_text_shows_faster_trend() -> None:
    out = format_diff(_diff(duration_delta=-3.0), fmt="text")
    assert "FASTER" in out


def test_text_shows_status_changed() -> None:
    out = format_diff(_diff(exit_code_b=1, status_changed=True), fmt="text")
    assert "CHANGED" in out


def test_text_na_when_duration_none() -> None:
    out = format_diff(_diff(duration_a=None, duration_b=None, duration_delta=None), fmt="text")
    assert "n/a" in out


def test_json_format_is_valid_json() -> None:
    out = format_diff(_diff(), fmt="json")
    data = json.loads(out)
    assert isinstance(data, dict)


def test_json_contains_expected_keys() -> None:
    out = format_diff(_diff(), fmt="json")
    data = json.loads(out)
    for key in ("job_name", "run_id_a", "run_id_b", "duration_delta", "status_changed"):
        assert key in data


def test_json_slower_flag() -> None:
    out = format_diff(_diff(duration_delta=5.0), fmt="json")
    data = json.loads(out)
    assert data["slower"] is True
    assert data["faster"] is False
