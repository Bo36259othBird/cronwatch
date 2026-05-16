"""Tests for RunReplayer and replay_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_replay import RunReplayer, ReplayCandidate
from cronwatch.replay_formatter import format_replay


def _utc(hour: int = 12, minute: int = 0) -> datetime:
    return datetime(2024, 1, 15, hour, minute, 0, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def replayer(store):
    return RunReplayer(store, lookback=20)


def _add_run(store, job, exit_code, hour=12):
    run_id = store.record_start(job, _utc(hour))
    store.record_finish(run_id, _utc(hour, 5), exit_code)
    return run_id


def test_candidates_empty_when_no_runs(store, replayer):
    assert replayer.candidates("backup") == []


def test_candidates_excludes_successful_runs(store, replayer):
    _add_run(store, "backup", exit_code=0)
    assert replayer.candidates("backup") == []


def test_candidates_includes_failed_runs(store, replayer):
    _add_run(store, "backup", exit_code=1)
    result = replayer.candidates("backup")
    assert len(result) == 1
    assert result[0].exit_code == 1
    assert result[0].job_name == "backup"


def test_candidates_returns_replay_candidate_instances(store, replayer):
    _add_run(store, "sync", exit_code=2)
    result = replayer.candidates("sync")
    assert isinstance(result[0], ReplayCandidate)


def test_latest_failure_returns_none_when_no_failures(store, replayer):
    _add_run(store, "cleanup", exit_code=0)
    assert replayer.latest_failure("cleanup") is None


def test_latest_failure_returns_most_recent(store, replayer):
    _add_run(store, "cleanup", exit_code=1, hour=10)
    _add_run(store, "cleanup", exit_code=1, hour=14)
    latest = replayer.latest_failure("cleanup")
    assert latest is not None
    assert latest.started_at.hour == 14


def test_is_failure_property(store, replayer):
    _add_run(store, "job", exit_code=127)
    c = replayer.candidates("job")[0]
    assert c.is_failure is True


def test_format_replay_text_no_candidates():
    out = format_replay([])
    assert "No replay candidates" in out


def test_format_replay_text_contains_job_name(store, replayer):
    _add_run(store, "nightly", exit_code=1)
    candidates = replayer.candidates("nightly")
    out = format_replay(candidates, fmt="text")
    assert "nightly" in out


def test_format_replay_json_is_valid(store, replayer):
    _add_run(store, "report", exit_code=3)
    candidates = replayer.candidates("report")
    out = format_replay(candidates, fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["exit_code"] == 3
