"""Tests for RunGrouper and group_formatter."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_grouper import Bucket, RunGrouper
from cronwatch.group_formatter import format_groups


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def grouper(store):
    return RunGrouper(store)


def _add_run(store: JobStore, job: str, dt: datetime, exit_code: int = 0) -> None:
    run_id = store.record_start(job, dt)
    store.record_finish(run_id, exit_code, dt)


# ── RunGrouper ────────────────────────────────────────────────────────────────

def test_group_empty_store_returns_empty(grouper):
    result = grouper.group("backup", Bucket.DAY)
    assert result == {}


def test_group_by_day_single_day(store, grouper):
    day = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
    _add_run(store, "backup", day)
    _add_run(store, "backup", day.replace(hour=14))
    groups = grouper.group("backup", Bucket.DAY)
    assert len(groups) == 1
    assert "2024-06-01" in groups
    assert groups["2024-06-01"].count == 2


def test_group_by_day_multiple_days(store, grouper):
    _add_run(store, "sync", datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc))
    _add_run(store, "sync", datetime(2024, 6, 2, 9, 0, tzinfo=timezone.utc))
    groups = grouper.group("sync", Bucket.DAY)
    assert len(groups) == 2


def test_group_by_hour(store, grouper):
    _add_run(store, "job", datetime(2024, 6, 1, 8, 15, tzinfo=timezone.utc))
    _add_run(store, "job", datetime(2024, 6, 1, 8, 45, tzinfo=timezone.utc))
    _add_run(store, "job", datetime(2024, 6, 1, 9, 5, tzinfo=timezone.utc))
    groups = grouper.group("job", Bucket.HOUR)
    assert len(groups) == 2
    assert groups["2024-06-01T08"].count == 2
    assert groups["2024-06-01T09"].count == 1


def test_group_by_week(store, grouper):
    _add_run(store, "report", datetime(2024, 6, 3, 12, 0, tzinfo=timezone.utc))  # W23
    _add_run(store, "report", datetime(2024, 6, 10, 12, 0, tzinfo=timezone.utc))  # W24
    groups = grouper.group("report", Bucket.WEEK)
    assert len(groups) == 2


def test_failure_count_in_group(store, grouper):
    dt = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
    run_id = store.record_start("job", dt)
    store.record_finish(run_id, 1, dt)  # failure
    _add_run(store, "job", dt.replace(hour=11), exit_code=0)
    groups = grouper.group("job", Bucket.DAY)
    grp = groups["2024-06-01"]
    assert grp.failure_count == 1
    assert grp.success_rate == pytest.approx(0.5)


# ── group_formatter ───────────────────────────────────────────────────────────

def test_text_format_contains_job_name(store, grouper):
    _add_run(store, "cleanup", datetime(2024, 6, 1, 6, 0, tzinfo=timezone.utc))
    groups = grouper.group("cleanup", Bucket.DAY)
    out = format_groups(groups, "cleanup", fmt="text")
    assert "cleanup" in out


def test_text_format_shows_bucket_key(store, grouper):
    _add_run(store, "cleanup", datetime(2024, 6, 1, 6, 0, tzinfo=timezone.utc))
    groups = grouper.group("cleanup", Bucket.DAY)
    out = format_groups(groups, "cleanup", fmt="text")
    assert "2024-06-01" in out


def test_json_format_is_valid(store, grouper):
    _add_run(store, "etl", datetime(2024, 6, 1, 3, 0, tzinfo=timezone.utc))
    groups = grouper.group("etl", Bucket.DAY)
    out = format_groups(groups, "etl", fmt="json")
    data = json.loads(out)
    assert data["job"] == "etl"
    assert len(data["groups"]) == 1
    assert data["groups"][0]["count"] == 1
