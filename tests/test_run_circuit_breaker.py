"""Tests for RunCircuitBreaker."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_circuit_breaker import CircuitState, RunCircuitBreaker


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def breaker(store):
    return RunCircuitBreaker(store, threshold=0.5, window=4)


def _utc(year=2024, month=1, day=1, hour=0):
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


def _add_run(store, job, exit_code, start=None, end=None):
    start = start or _utc()
    end = end or _utc(hour=1)
    run_id = store.record_start(job, start)
    store.record_finish(run_id, end, exit_code)
    return run_id


def test_evaluate_returns_circuit_state(store, breaker):
    state = breaker.evaluate("backup")
    assert isinstance(state, CircuitState)


def test_no_runs_circuit_is_closed(store, breaker):
    state = breaker.evaluate("backup")
    assert state.is_open is False
    assert state.total_count == 0


def test_all_successes_circuit_closed(store, breaker):
    for _ in range(4):
        _add_run(store, "backup", exit_code=0)
    state = breaker.evaluate("backup")
    assert state.is_open is False
    assert state.failure_rate == 0.0


def test_majority_failures_trips_circuit(store, breaker):
    _add_run(store, "backup", exit_code=1)
    _add_run(store, "backup", exit_code=1)
    _add_run(store, "backup", exit_code=0)
    _add_run(store, "backup", exit_code=1)
    state = breaker.evaluate("backup")
    assert state.is_open is True
    assert state.failure_count == 3
    assert state.total_count == 4


def test_tripped_at_set_when_open(store, breaker):
    for _ in range(3):
        _add_run(store, "sync", exit_code=1)
    _add_run(store, "sync", exit_code=1)
    state = breaker.evaluate("sync")
    assert state.tripped_at is not None


def test_tripped_at_cleared_on_recovery(store, breaker):
    for _ in range(4):
        _add_run(store, "sync", exit_code=1)
    breaker.evaluate("sync")  # trips it
    # replace store data with all successes via a new store fixture approach
    # re-evaluate after clearing failures by adding many successes
    # Use a fresh breaker with window=4 — add 4 successes to dominate window
    store2 = store  # same db
    for _ in range(4):
        _add_run(store2, "sync", exit_code=0)
    state = breaker.evaluate("sync")
    assert state.is_open is False
    assert state.tripped_at is None


def test_open_circuits_filters_closed(store, breaker):
    _add_run(store, "job_a", exit_code=0)
    for _ in range(4):
        _add_run(store, "job_b", exit_code=1)
    results = breaker.open_circuits(["job_a", "job_b"])
    assert len(results) == 1
    assert results[0].job_name == "job_b"


def test_failure_rate_property():
    state = CircuitState(
        job_name="x",
        is_open=True,
        failure_count=3,
        total_count=4,
        tripped_at=None,
        threshold=0.5,
    )
    assert state.failure_rate == pytest.approx(0.75)


def test_invalid_threshold_raises():
    with pytest.raises(ValueError):
        RunCircuitBreaker(None, threshold=0.0)


def test_invalid_window_raises():
    with pytest.raises(ValueError):
        RunCircuitBreaker(None, threshold=0.5, window=0)
