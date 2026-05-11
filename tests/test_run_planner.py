"""Tests for cronwatch.run_planner."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import JobConfig
from cronwatch.run_planner import RunPlan, RunPlanner
from cronwatch.store import JobStore


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _job(schedule: str = "*/5 * * * *") -> JobConfig:
    return JobConfig(name="backup", schedule=schedule, silence_threshold=600)


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def planner(store):
    return RunPlanner(store)


# ---------------------------------------------------------------------------
# RunPlan dataclass helpers
# ---------------------------------------------------------------------------

def test_run_plan_is_imminent_true():
    plan = RunPlan(
        job_name="j",
        last_run=None,
        next_expected=None,
        is_overdue=False,
        seconds_until_due=30.0,
    )
    assert plan.is_imminent(window_seconds=60) is True


def test_run_plan_is_imminent_false_when_far():
    plan = RunPlan(
        job_name="j",
        last_run=None,
        next_expected=None,
        is_overdue=False,
        seconds_until_due=300.0,
    )
    assert plan.is_imminent(window_seconds=60) is False


def test_run_plan_is_imminent_false_when_none():
    plan = RunPlan(
        job_name="j",
        last_run=None,
        next_expected=None,
        is_overdue=False,
        seconds_until_due=None,
    )
    assert plan.is_imminent() is False


# ---------------------------------------------------------------------------
# RunPlanner.plan
# ---------------------------------------------------------------------------

def test_plan_returns_run_plan_instance(planner):
    plan = planner.plan(_job())
    assert isinstance(plan, RunPlan)


def test_plan_job_name_matches(planner):
    plan = planner.plan(_job())
    assert plan.job_name == "backup"


def test_plan_no_last_run_when_store_empty(planner):
    plan = planner.plan(_job())
    assert plan.last_run is None


def test_plan_records_last_run_from_store(store, planner):
    run_id = store.record_start("backup", _utc(2024, 1, 10, 12, 0, 0))
    store.record_finish(run_id, exit_code=0, ended_at=_utc(2024, 1, 10, 12, 1, 0))
    plan = planner.plan(_job(), now=_utc(2024, 1, 10, 12, 30, 0))
    assert plan.last_run is not None
    assert plan.last_run.year == 2024


def test_plan_all_returns_list_of_plans(planner):
    jobs = [_job("*/5 * * * *"), JobConfig(name="sync", schedule="0 * * * *", silence_threshold=3600)]
    plans = planner.plan_all(jobs)
    assert len(plans) == 2
    assert {p.job_name for p in plans} == {"backup", "sync"}
