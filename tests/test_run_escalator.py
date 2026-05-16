"""Tests for RunEscalator."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronwatch.store import JobStore
from cronwatch.run_escalator import EscalationLevel, EscalationPolicy, RunEscalator


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def escalator(store):
    policy = EscalationPolicy(warning_threshold=2, critical_threshold=4)
    return RunEscalator(store, policy)


def _utc(year=2024, month=1, day=1, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def _add_run(store, job, exit_code, start=None, finish=None):
    start = start or _utc()
    finish = finish or _utc(hour=1)
    rid = store.record_start(job, start)
    store.record_finish(rid, finish, exit_code)
    return rid


def test_evaluate_returns_escalation_level(store, escalator):
    result = escalator.evaluate("myjob")
    assert isinstance(result, EscalationLevel)


def test_no_runs_is_normal(store, escalator):
    lvl = escalator.evaluate("myjob")
    assert lvl.level == 0
    assert lvl.label == "normal"
    assert lvl.consecutive_failures == 0


def test_single_success_is_normal(store, escalator):
    _add_run(store, "myjob", 0)
    lvl = escalator.evaluate("myjob")
    assert lvl.level == 0


def test_below_warning_threshold_is_normal(store, escalator):
    _add_run(store, "myjob", 1, _utc(hour=0), _utc(hour=1))
    lvl = escalator.evaluate("myjob")
    assert lvl.level == 0
    assert lvl.consecutive_failures == 1


def test_at_warning_threshold_is_warning(store, escalator):
    _add_run(store, "myjob", 1, _utc(hour=0), _utc(hour=1))
    _add_run(store, "myjob", 1, _utc(hour=2), _utc(hour=3))
    lvl = escalator.evaluate("myjob")
    assert lvl.level == 1
    assert lvl.label == "warning"


def test_at_critical_threshold_is_critical(store, escalator):
    for h in range(4):
        _add_run(store, "myjob", 1, _utc(hour=h * 2), _utc(hour=h * 2 + 1))
    lvl = escalator.evaluate("myjob")
    assert lvl.level == 2
    assert lvl.label == "critical"


def test_success_resets_consecutive_count(store, escalator):
    _add_run(store, "myjob", 1, _utc(hour=0), _utc(hour=1))
    _add_run(store, "myjob", 1, _utc(hour=2), _utc(hour=3))
    _add_run(store, "myjob", 0, _utc(hour=4), _utc(hour=5))  # success resets
    _add_run(store, "myjob", 1, _utc(hour=6), _utc(hour=7))
    lvl = escalator.evaluate("myjob")
    assert lvl.consecutive_failures == 1
    assert lvl.level == 0


def test_evaluate_all_returns_dict(store, escalator):
    _add_run(store, "job_a", 0)
    _add_run(store, "job_b", 1, _utc(hour=0), _utc(hour=1))
    _add_run(store, "job_b", 1, _utc(hour=2), _utc(hour=3))
    result = escalator.evaluate_all(["job_a", "job_b"])
    assert "job_a" in result
    assert result["job_a"].level == 0
    assert result["job_b"].level == 1


def test_is_elevated_false_when_normal(store, escalator):
    lvl = escalator.evaluate("myjob")
    assert not lvl.is_elevated


def test_is_elevated_true_when_warning(store, escalator):
    _add_run(store, "myjob", 1, _utc(hour=0), _utc(hour=1))
    _add_run(store, "myjob", 1, _utc(hour=2), _utc(hour=3))
    lvl = escalator.evaluate("myjob")
    assert lvl.is_elevated


def test_is_elevated_true_when_critical(store, escalator):
    for h in range(4):
        _add_run(store, "myjob", 1, _utc(hour=h * 2), _utc(hour=h * 2 + 1))
    lvl = escalator.evaluate("myjob")
    assert lvl.is_elevated
