"""Tests for cronwatch.retention."""
from __future__ import annotations

import time
from datetime import datetime, timedelta

import pytest

from cronwatch.retention import RetentionManager, RetentionPolicy
from cronwatch.store import JobStore


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


def _add_run(store: JobStore, job: str, age_days: float, success: bool = True) -> None:
    """Insert a completed run with a back-dated timestamp."""
    started = datetime.utcnow() - timedelta(days=age_days)
    run_id = store.record_start(job, started)
    finished = started + timedelta(seconds=1)
    store.record_finish(run_id, success=success, exit_code=0 if success else 1, finished_at=finished)


# ---------------------------------------------------------------------------
# prune by age
# ---------------------------------------------------------------------------

def test_prune_removes_old_records(store):
    _add_run(store, "job_a", age_days=40)
    _add_run(store, "job_a", age_days=5)
    policy = RetentionPolicy(max_age_days=30)
    manager = RetentionManager(store, policy)
    deleted = manager.prune()
    assert deleted == 1


def test_prune_keeps_recent_records(store):
    _add_run(store, "job_b", age_days=10)
    policy = RetentionPolicy(max_age_days=30)
    manager = RetentionManager(store, policy)
    deleted = manager.prune()
    assert deleted == 0


def test_prune_returns_zero_on_empty_store(store):
    policy = RetentionPolicy(max_age_days=30)
    manager = RetentionManager(store, policy)
    assert manager.prune() == 0


# ---------------------------------------------------------------------------
# prune by count
# ---------------------------------------------------------------------------

def test_prune_by_count_keeps_n_newest(store):
    for i in range(5):
        _add_run(store, "job_c", age_days=float(5 - i))
    policy = RetentionPolicy(max_age_days=365, max_runs_per_job=3)
    manager = RetentionManager(store, policy)
    deleted = manager.prune()
    assert deleted == 2
    runs = store.get_runs("job_c")
    assert len(runs) == 3


def test_prune_by_count_no_op_when_under_limit(store):
    _add_run(store, "job_d", age_days=1)
    _add_run(store, "job_d", age_days=2)
    policy = RetentionPolicy(max_age_days=365, max_runs_per_job=5)
    manager = RetentionManager(store, policy)
    assert manager.prune() == 0


# ---------------------------------------------------------------------------
# combined
# ---------------------------------------------------------------------------

def test_prune_combined_age_and_count(store):
    _add_run(store, "job_e", age_days=40)   # too old -> deleted by age
    for i in range(4):
        _add_run(store, "job_e", age_days=float(i + 1))  # 4 recent runs
    policy = RetentionPolicy(max_age_days=30, max_runs_per_job=2)
    manager = RetentionManager(store, policy)
    deleted = manager.prune()
    assert deleted == 3  # 1 by age + 2 by count
    assert len(store.get_runs("job_e")) == 2
