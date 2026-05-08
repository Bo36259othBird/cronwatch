"""Tests for cronwatch.run_classifier."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from cronwatch.store import JobRun
from cronwatch.run_classifier import (
    RunClassifier,
    RunClassification,
    CLASS_SUCCESS_FAST,
    CLASS_SUCCESS_NORMAL,
    CLASS_SUCCESS_SLOW,
    CLASS_FAILURE,
    CLASS_INCOMPLETE,
)


def _utc(offset_seconds: float = 0.0) -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


def _run(
    exit_code: int = 0,
    duration: float | None = 120.0,
    run_id: int = 1,
) -> JobRun:
    started = _utc()
    finished = _utc(duration) if duration is not None else None
    return JobRun(
        id=run_id,
        job_name="backup",
        started_at=started,
        finished_at=finished,
        exit_code=exit_code,
    )


@pytest.fixture
def classifier() -> RunClassifier:
    return RunClassifier(fast_threshold=60.0, slow_threshold=300.0)


def test_classify_returns_run_classification(classifier):
    result = classifier.classify(_run())
    assert isinstance(result, RunClassification)


def test_classify_fast_success(classifier):
    result = classifier.classify(_run(duration=30.0))
    assert result.category == CLASS_SUCCESS_FAST
    assert result.is_success


def test_classify_normal_success(classifier):
    result = classifier.classify(_run(duration=120.0))
    assert result.category == CLASS_SUCCESS_NORMAL
    assert result.is_success


def test_classify_slow_success(classifier):
    result = classifier.classify(_run(duration=400.0))
    assert result.category == CLASS_SUCCESS_SLOW
    assert result.is_success


def test_classify_failure(classifier):
    result = classifier.classify(_run(exit_code=1, duration=50.0))
    assert result.category == CLASS_FAILURE
    assert not result.is_success


def test_classify_incomplete_run(classifier):
    result = classifier.classify(_run(duration=None))
    assert result.category == CLASS_INCOMPLETE
    assert result.duration_seconds is None
    assert not result.is_success


def test_classify_stores_duration(classifier):
    result = classifier.classify(_run(duration=90.0))
    assert result.duration_seconds == pytest.approx(90.0)


def test_classify_all_returns_list(classifier):
    runs = [_run(run_id=i, duration=float(i * 10)) for i in range(1, 4)]
    results = classifier.classify_all(runs)
    assert len(results) == 3
    assert all(isinstance(r, RunClassification) for r in results)


def test_boundary_exactly_fast_threshold(classifier):
    result = classifier.classify(_run(duration=60.0))
    assert result.category == CLASS_SUCCESS_FAST


def test_boundary_exactly_slow_threshold(classifier):
    result = classifier.classify(_run(duration=300.0))
    assert result.category == CLASS_SUCCESS_SLOW
