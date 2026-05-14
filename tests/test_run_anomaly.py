"""Tests for RunAnomalyDetector."""
from __future__ import annotations

import datetime
import pytest

from cronwatch.store import JobStore
from cronwatch.run_anomaly import AnomalyResult, RunAnomalyDetector


@pytest.fixture
def store(tmp_path):
    return JobStore(tmp_path / "test.db")


@pytest.fixture
def detector(store):
    return RunAnomalyDetector(store, threshold=2.0, min_samples=3)


def _utc(**kwargs):
    return datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(**kwargs)


def _add_run(store, job_name, start, duration_s, success=True):
    run_id = store.record_start(job_name, _utc(seconds=start))
    store.record_finish(
        run_id,
        finished_at=_utc(seconds=start + duration_s),
        exit_code=0 if success else 1,
    )
    return run_id


def test_analyze_returns_none_when_insufficient_data(store, detector):
    _add_run(store, "job", 0, 10)
    _add_run(store, "job", 20, 11)
    # only 2 runs — below min_samples=3
    run_id = _add_run(store, "job", 40, 12)
    # min_samples not yet met for analysis with 3 when we need >3 ... actually 3==3
    # Let's use a detector with min_samples=5
    det5 = RunAnomalyDetector(store, threshold=2.0, min_samples=5)
    result = det5.analyze("job", run_id)
    assert result is None


def test_analyze_returns_anomaly_result(store, detector):
    _add_run(store, "job", 0, 10)
    _add_run(store, "job", 20, 10)
    run_id = _add_run(store, "job", 40, 10)
    result = detector.analyze("job", run_id)
    assert isinstance(result, AnomalyResult)


def test_analyze_normal_run_is_not_anomaly(store, detector):
    for i in range(5):
        _add_run(store, "job", i * 20, 10)
    run_id = _add_run(store, "job", 100, 10)
    result = detector.analyze("job", run_id)
    assert result is not None
    assert result.is_anomaly is False


def test_analyze_slow_run_is_anomaly(store, detector):
    # Establish tight cluster then add outlier
    for i in range(4):
        _add_run(store, "job", i * 30, 10)
    run_id = _add_run(store, "job", 200, 9999)
    result = detector.analyze("job", run_id)
    assert result is not None
    assert result.is_anomaly is True
    assert result.z_score > 2.0


def test_analyze_returns_none_for_missing_run(store, detector):
    result = detector.analyze("job", 9999)
    assert result is None


def test_anomalies_returns_empty_for_insufficient_data(store, detector):
    _add_run(store, "job", 0, 10)
    result = detector.anomalies("job")
    assert result == []


def test_anomalies_finds_outlier_runs(store, detector):
    for i in range(4):
        _add_run(store, "job", i * 30, 10)
    _add_run(store, "job", 200, 9999)
    results = detector.anomalies("job")
    assert len(results) == 1
    assert results[0].is_anomaly is True


def test_deviation_pct_is_positive_for_slow_run(store, detector):
    for i in range(4):
        _add_run(store, "job", i * 30, 10)
    run_id = _add_run(store, "job", 200, 9999)
    result = detector.analyze("job", run_id)
    assert result is not None
    assert result.deviation_pct > 0
