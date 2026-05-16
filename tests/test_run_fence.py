"""Tests for cronwatch.run_fence."""
from __future__ import annotations

import pytest

from cronwatch.store import JobStore
from cronwatch.run_fence import FenceViolation, RunFence


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test.db"
    return JobStore(str(db))


@pytest.fixture
def fence(store):
    return RunFence(store, default_limit=1)


def _start(store: JobStore, job_name: str) -> int:
    return store.record_start(job_name)


def _finish(store: JobStore, run_id: int, exit_code: int = 0) -> None:
    store.record_finish(run_id, exit_code)


# ---------------------------------------------------------------------------
# FenceViolation helpers
# ---------------------------------------------------------------------------

def test_fence_violation_excess():
    v = FenceViolation(job_name="backup", active_count=3, limit=1)
    assert v.excess == 2


def test_fence_violation_is_violation_true():
    v = FenceViolation(job_name="backup", active_count=2, limit=1)
    assert v.is_violation is True


def test_fence_violation_is_violation_false():
    v = FenceViolation(job_name="backup", active_count=1, limit=1)
    assert v.is_violation is False


# ---------------------------------------------------------------------------
# RunFence.check
# ---------------------------------------------------------------------------

def test_check_no_runs_not_a_violation(store, fence):
    v = fence.check("nightly")
    assert v.is_violation is False
    assert v.active_count == 0


def test_check_one_active_within_default_limit(store, fence):
    _start(store, "nightly")
    v = fence.check("nightly")
    assert v.is_violation is False
    assert v.active_count == 1


def test_check_two_active_exceeds_default_limit(store, fence):
    _start(store, "nightly")
    _start(store, "nightly")
    v = fence.check("nightly")
    assert v.is_violation is True
    assert v.active_count == 2
    assert v.excess == 1


def test_check_finished_run_not_counted(store, fence):
    run_id = _start(store, "nightly")
    _finish(store, run_id)
    v = fence.check("nightly")
    assert v.is_violation is False
    assert v.active_count == 0


# ---------------------------------------------------------------------------
# RunFence.set_limit / per-job override
# ---------------------------------------------------------------------------

def test_set_limit_allows_higher_concurrency(store, fence):
    fence.set_limit("parallel_job", 3)
    _start(store, "parallel_job")
    _start(store, "parallel_job")
    v = fence.check("parallel_job")
    assert v.is_violation is False


def test_set_limit_raises_on_zero():
    store_dummy = object()
    f = RunFence.__new__(RunFence)
    f._store = store_dummy
    f._default_limit = 1
    f._limits = {}
    with pytest.raises(ValueError):
        f.set_limit("job", 0)


# ---------------------------------------------------------------------------
# RunFence.violations
# ---------------------------------------------------------------------------

def test_violations_returns_only_exceeding_jobs(store, fence):
    _start(store, "job_a")
    _start(store, "job_a")  # exceeds limit=1
    _start(store, "job_b")  # within limit
    result = fence.violations(["job_a", "job_b"])
    assert len(result) == 1
    assert result[0].job_name == "job_a"


def test_violations_empty_when_all_within_limits(store, fence):
    _start(store, "job_a")
    result = fence.violations(["job_a"])
    assert result == []


def test_constructor_raises_on_invalid_default_limit(store):
    with pytest.raises(ValueError):
        RunFence(store, default_limit=0)
