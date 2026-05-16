"""Tests for RunPinner and pinned_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_pinned import PinnedRun, RunPinner
from cronwatch.pinned_formatter import format_pins


def _utc(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, 0, tzinfo=timezone.utc)


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def pinner(store):
    return RunPinner(store)


def _add_run(store, job, start_h, end_h, exit_code=0):
    run_id = store.record_start(job, _utc(start_h))
    store.record_finish(run_id, _utc(end_h), exit_code)
    return run_id


# --- RunPinner ---

def test_slowest_no_runs_returns_none(store, pinner):
    assert pinner.slowest("backup") is None


def test_fastest_no_runs_returns_none(store, pinner):
    assert pinner.fastest("backup") is None


def test_first_failure_no_runs_returns_none(store, pinner):
    assert pinner.first_failure("backup") is None


def test_slowest_returns_pinned_run(store, pinner):
    _add_run(store, "backup", 1, 2)   # 1 h
    _add_run(store, "backup", 3, 6)   # 3 h  <- slowest
    pin = pinner.slowest("backup")
    assert isinstance(pin, PinnedRun)
    assert pin.reason == "slowest"
    assert pin.duration == pytest.approx(3 * 3600)


def test_fastest_returns_pinned_run(store, pinner):
    _add_run(store, "backup", 1, 2)   # 1 h
    _add_run(store, "backup", 3, 6)   # 3 h
    pin = pinner.fastest("backup")
    assert pin.reason == "fastest"
    assert pin.duration == pytest.approx(3600)


def test_first_failure_returns_correct_run(store, pinner):
    _add_run(store, "backup", 1, 2, exit_code=0)
    fail_id = _add_run(store, "backup", 3, 4, exit_code=1)
    _add_run(store, "backup", 5, 6, exit_code=1)
    pin = pinner.first_failure("backup")
    assert pin.run_id == fail_id
    assert pin.is_failure()


def test_all_pins_returns_list(store, pinner):
    _add_run(store, "backup", 1, 2)
    _add_run(store, "backup", 3, 5, exit_code=1)
    pins = pinner.all_pins("backup")
    reasons = {p.reason for p in pins}
    assert "slowest" in reasons
    assert "fastest" in reasons
    assert "first_failure" in reasons


# --- format_pins ---

def test_format_text_no_pins():
    out = format_pins([])
    assert "No pinned" in out


def test_format_text_contains_reason(store, pinner):
    _add_run(store, "sync", 1, 3)
    pins = pinner.all_pins("sync")
    out = format_pins(pins, fmt="text")
    assert "slowest" in out
    assert "fastest" in out


def test_format_json_is_valid(store, pinner):
    _add_run(store, "sync", 1, 2)
    pins = pinner.all_pins("sync")
    out = format_pins(pins, fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert all("reason" in item for item in data)


def test_format_json_failure_flag(store, pinner):
    _add_run(store, "sync", 1, 2, exit_code=2)
    pins = pinner.all_pins("sync")
    out = format_pins(pins, fmt="json")
    data = json.loads(out)
    failures = [d for d in data if d["reason"] == "first_failure"]
    assert failures
