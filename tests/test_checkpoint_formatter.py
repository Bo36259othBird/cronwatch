"""Tests for checkpoint_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.run_checkpoint import Checkpoint, CheckpointSummary
from cronwatch.checkpoint_formatter import format_checkpoints


def _utc(hour: int = 10) -> datetime:
    return datetime(2024, 6, 1, hour, 0, 0, tzinfo=timezone.utc)


def _make_summary(run_id: int = 1, job_name: str = "backup",
                  names: list[str] | None = None) -> CheckpointSummary:
    names = names or ["init", "process", "done"]
    checkpoints = [
        Checkpoint(run_id=run_id, job_name=job_name, name=n,
                   reached_at=_utc(i + 8), metadata={})
        for i, n in enumerate(names)
    ]
    return CheckpointSummary(run_id=run_id, job_name=job_name, checkpoints=checkpoints)


def test_text_contains_job_name():
    s = _make_summary()
    out = format_checkpoints([s], fmt="text")
    assert "backup" in out


def test_text_contains_checkpoint_names():
    s = _make_summary(names=["step_a", "step_b"])
    out = format_checkpoints([s], fmt="text")
    assert "step_a" in out
    assert "step_b" in out


def test_text_shows_run_id():
    s = _make_summary(run_id=42)
    out = format_checkpoints([s], fmt="text")
    assert "42" in out


def test_text_empty_list_shows_placeholder():
    out = format_checkpoints([], fmt="text")
    assert "No checkpoints" in out


def test_text_summary_with_no_checkpoints_shows_none():
    s = CheckpointSummary(run_id=1, job_name="job", checkpoints=[])
    out = format_checkpoints([s], fmt="text")
    assert "(none)" in out


def test_json_format_is_valid_json():
    s = _make_summary()
    out = format_checkpoints([s], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1


def test_json_contains_expected_fields():
    s = _make_summary(run_id=7, job_name="sync")
    data = json.loads(format_checkpoints([s], fmt="json"))
    entry = data[0]
    assert entry["run_id"] == 7
    assert entry["job_name"] == "sync"
    assert "checkpoints" in entry
    assert entry["checkpoint_count"] == 3


def test_json_checkpoint_entries_have_name_and_time():
    s = _make_summary(names=["go"])
    data = json.loads(format_checkpoints([s], fmt="json"))
    cp = data[0]["checkpoints"][0]
    assert cp["name"] == "go"
    assert "reached_at" in cp
