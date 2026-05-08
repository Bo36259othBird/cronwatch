"""Tests for RunBaselineCollector and Baseline."""
from __future__ import annotations

import datetime
import pytest

from cronwatch.store import JobStore
from cronwatch.run_baseline import Baseline, RunBaselineCollector
from cronwatch.baseline_formatter import format_baselines


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def collector(store):
    return RunBaselineCollector(store)


def _utc(hour: int = 0) -> datetime.datetime:
    return datetime.datetime(2024, 1, 1, hour, 0, 0, tzinfo=datetime.timezone.utc)


def _add_run(store: JobStore, job: str, duration: float) -> None:
    run_id = store.record_start(job, _utc())
    store.record_finish(run_id, exit_code=0, ended_at=_utc() + datetime.timedelta(seconds=duration))


# --- Baseline model ---

def test_baseline_no_data_returns_none_fields(collector):
    b = collector.collect("missing_job")
    assert b.mean_duration is None
    assert b.std_duration is None
    assert b.sample_size == 0


def test_baseline_fewer_than_min_samples(store, collector):
    _add_run(store, "job_a", 10.0)
    _add_run(store, "job_a", 12.0)
    b = collector.collect("job_a")
    assert b.mean_duration is None  # below _MIN_SAMPLES=3
    assert b.sample_size == 2


def test_baseline_computes_mean(store, collector):
    for d in [10.0, 20.0, 30.0]:
        _add_run(store, "job_b", d)
    b = collector.collect("job_b")
    assert b.mean_duration == pytest.approx(20.0)


def test_baseline_std_is_non_negative(store, collector):
    for d in [10.0, 20.0, 30.0]:
        _add_run(store, "job_b", d)
    b = collector.collect("job_b")
    assert b.std_duration is not None
    assert b.std_duration >= 0.0


def test_within_bounds_true_for_mean(store, collector):
    for d in [10.0, 10.0, 10.0]:
        _add_run(store, "job_c", d)
    b = collector.collect("job_c")
    assert b.within_bounds(10.0) is True


def test_within_bounds_false_for_extreme_outlier(store, collector):
    for d in [10.0, 10.0, 10.0]:
        _add_run(store, "job_d", d)
    b = collector.collect("job_d")
    assert b.within_bounds(9999.0) is False


def test_within_bounds_true_when_no_baseline():
    b = Baseline(job_name="x", mean_duration=None, std_duration=None, sample_size=0)
    assert b.within_bounds(999.0) is True


# --- Formatter ---

def test_text_format_contains_job_name(store, collector):
    for d in [5.0, 10.0, 15.0]:
        _add_run(store, "job_e", d)
    b = collector.collect("job_e")
    output = format_baselines([b])
    assert "job_e" in output


def test_text_format_shows_na_when_no_data():
    b = Baseline(job_name="empty", mean_duration=None, std_duration=None, sample_size=0)
    output = format_baselines([b])
    assert "N/A" in output


def test_json_format_is_valid_json(store, collector):
    import json
    for d in [5.0, 10.0, 15.0]:
        _add_run(store, "job_f", d)
    b = collector.collect("job_f")
    output = format_baselines([b], fmt="json")
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["job_name"] == "job_f"
