"""Tests for RunMirror and mirror_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_mirror import RunMirror, MirrorResult
from cronwatch.mirror_formatter import format_mirror


def _utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def mirror(store):
    return RunMirror(store, divergence_threshold=0.10)


def _add_run(store, job: str, exit_code: int = 0):
    t = _utc(2024, 1, 1)
    run_id = store.record_start(job, t)
    store.record_finish(run_id, t, exit_code=exit_code)


def test_compare_no_runs_returns_not_diverged(store, mirror):
    result = mirror.compare("job_a", "job_b")
    assert isinstance(result, MirrorResult)
    assert result.diverged is False
    assert result.divergence_pct is None


def test_compare_identical_success_rates_not_diverged(store, mirror):
    for _ in range(5):
        _add_run(store, "job_a", exit_code=0)
        _add_run(store, "job_b", exit_code=0)
    result = mirror.compare("job_a", "job_b")
    assert result.diverged is False
    assert result.divergence_pct == 0.0


def test_compare_detects_divergence(store, mirror):
    for _ in range(10):
        _add_run(store, "job_a", exit_code=0)
    for _ in range(5):
        _add_run(store, "job_b", exit_code=0)
    for _ in range(5):
        _add_run(store, "job_b", exit_code=1)
    result = mirror.compare("job_a", "job_b")
    assert result.diverged is True
    assert result.divergence_pct is not None
    assert result.divergence_pct > 0


def test_compare_counts_runs_correctly(store, mirror):
    for _ in range(3):
        _add_run(store, "job_a", exit_code=0)
    _add_run(store, "job_a", exit_code=1)
    for _ in range(2):
        _add_run(store, "job_b", exit_code=0)
    result = mirror.compare("job_a", "job_b")
    assert result.runs_a == 4
    assert result.runs_b == 2
    assert result.failures_a == 1
    assert result.failures_b == 0


def test_success_rate_none_when_no_runs(store, mirror):
    result = mirror.compare("job_a", "job_b")
    assert result.success_rate_a is None
    assert result.success_rate_b is None


def test_format_text_contains_job_names(store, mirror):
    _add_run(store, "job_a")
    _add_run(store, "job_b")
    result = mirror.compare("job_a", "job_b")
    text = format_mirror(result, fmt="text")
    assert "job_a" in text
    assert "job_b" in text


def test_format_text_contains_header(store, mirror):
    result = mirror.compare("job_a", "job_b")
    text = format_mirror(result, fmt="text")
    assert "Mirror" in text


def test_format_json_is_valid(store, mirror):
    _add_run(store, "job_a")
    _add_run(store, "job_b")
    result = mirror.compare("job_a", "job_b")
    data = json.loads(format_mirror(result, fmt="json"))
    assert data["job_a"] == "job_a"
    assert "diverged" in data


def test_format_json_contains_divergence_pct(store, mirror):
    for _ in range(10):
        _add_run(store, "job_a", exit_code=0)
    for _ in range(5):
        _add_run(store, "job_b", exit_code=1)
    for _ in range(5):
        _add_run(store, "job_b", exit_code=0)
    result = mirror.compare("job_a", "job_b")
    data = json.loads(format_mirror(result, fmt="json"))
    assert data["divergence_pct"] is not None
