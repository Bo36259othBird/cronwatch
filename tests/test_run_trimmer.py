"""Tests for RunTrimmer."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from cronwatch.store import JobStore
from cronwatch.run_trimmer import RunTrimmer, TrimResult


def _utc(offset_seconds: float = 0) -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def trimmer(store):
    return RunTrimmer(store, z_threshold=2.0)


def _add_run(store, job_name, start_offset, duration, exit_code=0):
    run_id = store.record_start(job_name, _utc(start_offset))
    store.record_finish(run_id, exit_code, _utc(start_offset + duration))
    return run_id


def test_trim_returns_trim_result_instance(store, trimmer):
    result = trimmer.trim("backup")
    assert isinstance(result, TrimResult)


def test_trim_no_runs_returns_zero_counts(store, trimmer):
    result = trimmer.trim("backup")
    assert result.original_count == 0
    assert result.trimmed_count == 0
    assert result.removed_ids == []


def test_trim_fewer_than_three_runs_skips_outlier_detection(store, trimmer):
    _add_run(store, "backup", 0, 10)
    _add_run(store, "backup", 20, 12)
    result = trimmer.trim("backup")
    assert result.removed_ids == []
    assert result.mean_duration is None


def test_trim_normal_runs_returns_no_removals(store, trimmer):
    for i in range(5):
        _add_run(store, "backup", i * 30, 10 + i * 0.1)
    result = trimmer.trim("backup")
    assert result.removed_ids == []
    assert result.was_trimmed is False


def test_trim_detects_extreme_outlier(store, trimmer):
    # Five normal runs ~10s, one extreme outlier at 1000s
    for i in range(5):
        _add_run(store, "backup", i * 60, 10.0)
    outlier_id = _add_run(store, "backup", 400, 1000.0)
    result = trimmer.trim("backup")
    assert outlier_id in result.removed_ids
    assert result.was_trimmed is True


def test_trim_removed_count_matches_removed_ids(store, trimmer):
    for i in range(5):
        _add_run(store, "backup", i * 60, 10.0)
    _add_run(store, "backup", 400, 9999.0)
    result = trimmer.trim("backup")
    assert result.removed_count == len(result.removed_ids)


def test_trim_trimmed_count_is_original_minus_removed(store, trimmer):
    for i in range(5):
        _add_run(store, "backup", i * 60, 10.0)
    _add_run(store, "backup", 400, 9999.0)
    result = trimmer.trim("backup")
    assert result.trimmed_count == result.original_count - result.removed_count


def test_trim_mean_and_stdev_populated_with_enough_runs(store, trimmer):
    for i in range(6):
        _add_run(store, "backup", i * 30, 10.0 + i)
    result = trimmer.trim("backup")
    assert result.mean_duration is not None
    assert result.stdev_duration is not None


def test_trim_job_name_preserved(store, trimmer):
    result = trimmer.trim("my_job")
    assert result.job_name == "my_job"
