"""Tests for cronwatch.snapshot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.snapshot import JobSnapshot, Snapshot, SnapshotWriter, build_snapshot
from cronwatch.store import JobStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DT = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


class _FakeSilenceDetector:
    def __init__(self, silent):
        self._silent = silent

    def silent_jobs(self):
        return self._silent


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


# ---------------------------------------------------------------------------
# JobSnapshot / Snapshot dataclasses
# ---------------------------------------------------------------------------


def test_job_snapshot_fields():
    js = JobSnapshot(name="backup", last_run_at=None, last_exit_code=None,
                     last_duration_seconds=None, is_silent=False)
    assert js.name == "backup"
    assert js.is_silent is False


def test_snapshot_to_dict_round_trip():
    snap = Snapshot(
        captured_at="2024-01-15T10:00:00+00:00",
        jobs=[
            JobSnapshot("job1", "2024-01-15T09:00:00+00:00", 0, 12.5, False)
        ],
    )
    d = snap.to_dict()
    restored = Snapshot.from_dict(d)
    assert restored.captured_at == snap.captured_at
    assert len(restored.jobs) == 1
    assert restored.jobs[0].name == "job1"


# ---------------------------------------------------------------------------
# SnapshotWriter
# ---------------------------------------------------------------------------


def test_writer_creates_file(tmp_path):
    snap = Snapshot(captured_at="2024-01-15T10:00:00+00:00", jobs=[])
    writer = SnapshotWriter(str(tmp_path / "snap.json"))
    writer.write(snap)
    assert (tmp_path / "snap.json").exists()


def test_writer_read_returns_none_if_missing(tmp_path):
    writer = SnapshotWriter(str(tmp_path / "missing.json"))
    assert writer.read() is None


def test_writer_round_trip(tmp_path):
    snap = Snapshot(
        captured_at="2024-01-15T10:00:00+00:00",
        jobs=[JobSnapshot("nightly", None, None, None, True)],
    )
    writer = SnapshotWriter(str(tmp_path / "snap.json"))
    writer.write(snap)
    loaded = writer.read()
    assert loaded.jobs[0].is_silent is True


# ---------------------------------------------------------------------------
# build_snapshot
# ---------------------------------------------------------------------------


def test_build_snapshot_no_runs(store):
    detector = _FakeSilenceDetector([])
    snap = build_snapshot(["job_a"], store, detector)
    assert len(snap.jobs) == 1
    assert snap.jobs[0].last_exit_code is None
    assert snap.jobs[0].is_silent is False


def test_build_snapshot_marks_silent(store):
    detector = _FakeSilenceDetector(["job_a"])
    snap = build_snapshot(["job_a"], store, detector)
    assert snap.jobs[0].is_silent is True


def test_build_snapshot_with_completed_run(store):
    run_id = store.record_start("job_a", DT)
    store.record_finish(run_id, exit_code=0, finished_at=datetime(2024, 1, 15, 10, 0, 30, tzinfo=timezone.utc))
    detector = _FakeSilenceDetector([])
    snap = build_snapshot(["job_a"], store, detector)
    assert snap.jobs[0].last_exit_code == 0
    assert snap.jobs[0].last_duration_seconds == pytest.approx(30.0)
