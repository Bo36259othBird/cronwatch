"""Tests for RunHeatmapBuilder and heatmap_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_heatmap import RunHeatmap, RunHeatmapBuilder, DAYS
from cronwatch.heatmap_formatter import format_heatmap


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def builder(store):
    return RunHeatmapBuilder(store)


def _add_run(store: JobStore, job: str, dt: datetime, exit_code: int = 0) -> None:
    run_id = store.record_start(job, dt)
    store.record_finish(run_id, dt, exit_code)


def _utc(year, month, day, hour) -> datetime:
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


# --- Monday 2024-01-01 is a Monday (weekday=0) ---

def test_build_returns_heatmap_instance(builder):
    hm = builder.build("backup")
    assert isinstance(hm, RunHeatmap)
    assert hm.job_name == "backup"


def test_heatmap_has_168_cells(builder):
    hm = builder.build("backup")
    assert len(hm.cells) == 7 * 24


def test_empty_store_all_cells_zero(builder):
    hm = builder.build("backup")
    assert all(c.count == 0 for c in hm.cells)


def test_run_increments_correct_cell(store, builder):
    # 2024-01-01 is Monday, hour 14
    _add_run(store, "backup", _utc(2024, 1, 1, 14))
    hm = builder.build("backup")
    cell = hm.cell(0, 14)  # Monday=0, hour=14
    assert cell.count == 1
    assert cell.failure_count == 0


def test_failure_increments_failure_count(store, builder):
    _add_run(store, "backup", _utc(2024, 1, 1, 9), exit_code=1)
    hm = builder.build("backup")
    cell = hm.cell(0, 9)
    assert cell.count == 1
    assert cell.failure_count == 1


def test_failure_rate_computed(store, builder):
    _add_run(store, "backup", _utc(2024, 1, 1, 6), exit_code=0)
    _add_run(store, "backup", _utc(2024, 1, 1, 6), exit_code=1)
    hm = builder.build("backup")
    cell = hm.cell(0, 6)
    assert cell.failure_rate == pytest.approx(0.5)


def test_peak_hour_returns_busiest_hour(store, builder):
    for _ in range(3):
        _add_run(store, "backup", _utc(2024, 1, 1, 2))
    _add_run(store, "backup", _utc(2024, 1, 1, 10))
    hm = builder.build("backup")
    assert hm.peak_hour() == 2


def test_peak_hour_none_on_empty(builder):
    hm = builder.build("backup")
    assert hm.peak_hour() is None


def test_text_format_contains_job_name(store, builder):
    hm = builder.build("backup")
    out = format_heatmap(hm, fmt="text")
    assert "backup" in out


def test_text_format_contains_day_labels(store, builder):
    hm = builder.build("backup")
    out = format_heatmap(hm, fmt="text")
    for day in DAYS:
        assert day in out


def test_json_format_is_valid_json(store, builder):
    hm = builder.build("backup")
    out = format_heatmap(hm, fmt="json")
    data = json.loads(out)
    assert data["job_name"] == "backup"
    assert "cells" in data
    assert len(data["cells"]) == 168
