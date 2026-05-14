"""Tests for RunCheckpointer."""
from __future__ import annotations

import pytest
from datetime import timezone

from cronwatch.store import JobStore
from cronwatch.run_checkpoint import RunCheckpointer, Checkpoint, CheckpointSummary


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def checkpointer(store):
    return RunCheckpointer(store)


def _add_run(store: JobStore, job_name: str = "backup") -> int:
    run_id = store.record_start(job_name)
    store.record_finish(run_id, exit_code=0)
    return run_id


def test_record_returns_checkpoint_instance(store, checkpointer):
    run_id = _add_run(store)
    cp = checkpointer.record(run_id, "backup", "step_one")
    assert isinstance(cp, Checkpoint)
    assert cp.name == "step_one"
    assert cp.run_id == run_id


def test_record_stores_metadata(store, checkpointer):
    run_id = _add_run(store)
    cp = checkpointer.record(run_id, "backup", "upload", metadata={"bytes": "1024"})
    assert cp.metadata == {"bytes": "1024"}


def test_get_summary_no_checkpoints(store, checkpointer):
    run_id = _add_run(store)
    summary = checkpointer.get_summary(run_id, "backup")
    assert isinstance(summary, CheckpointSummary)
    assert summary.count == 0
    assert summary.last() is None


def test_get_summary_returns_all_checkpoints(store, checkpointer):
    run_id = _add_run(store)
    checkpointer.record(run_id, "backup", "start")
    checkpointer.record(run_id, "backup", "middle")
    checkpointer.record(run_id, "backup", "end")
    summary = checkpointer.get_summary(run_id, "backup")
    assert summary.count == 3
    assert summary.names() == ["start", "middle", "end"]


def test_get_summary_last_returns_final_checkpoint(store, checkpointer):
    run_id = _add_run(store)
    checkpointer.record(run_id, "backup", "alpha")
    checkpointer.record(run_id, "backup", "omega")
    summary = checkpointer.get_summary(run_id, "backup")
    assert summary.last().name == "omega"


def test_checkpoints_isolated_by_run_id(store, checkpointer):
    run_a = _add_run(store)
    run_b = _add_run(store)
    checkpointer.record(run_a, "backup", "only_a")
    summary_b = checkpointer.get_summary(run_b, "backup")
    assert summary_b.count == 0


def test_reached_at_is_timezone_aware(store, checkpointer):
    run_id = _add_run(store)
    checkpointer.record(run_id, "backup", "step")
    summary = checkpointer.get_summary(run_id, "backup")
    cp = summary.checkpoints[0]
    assert cp.reached_at.tzinfo is not None
