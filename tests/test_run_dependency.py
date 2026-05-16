"""Tests for RunDependencyChecker."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from cronwatch.store import JobStore
from cronwatch.run_dependency import DependencyGraph, DependencyViolation, RunDependencyChecker


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def graph():
    g = DependencyGraph()
    g.add("job_b", "job_a")
    return g


@pytest.fixture()
def checker(store, graph):
    return RunDependencyChecker(store, graph)


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _add_run(store: JobStore, name: str, exit_code: int = 0) -> int:
    run_id = store.record_start(name, _utc(2024, 1, 1, 10, 0, 0))
    store.record_finish(run_id, _utc(2024, 1, 1, 10, 1, 0), exit_code)
    return run_id


def test_check_no_runs_returns_empty(checker):
    assert checker.check("job_b") == []


def test_check_returns_violation_when_dep_never_ran(store, graph):
    _add_run(store, "job_b")
    checker = RunDependencyChecker(store, graph)
    violations = checker.check("job_b")
    assert len(violations) == 1
    assert violations[0].depends_on == "job_a"
    assert not violations[0].is_blocking


def test_check_no_violation_when_dep_succeeded(store, graph):
    _add_run(store, "job_a", exit_code=0)
    _add_run(store, "job_b", exit_code=0)
    checker = RunDependencyChecker(store, graph)
    violations = checker.check("job_b")
    assert violations == []


def test_check_violation_when_dep_failed(store, graph):
    _add_run(store, "job_a", exit_code=1)
    _add_run(store, "job_b", exit_code=0)
    checker = RunDependencyChecker(store, graph)
    violations = checker.check("job_b")
    assert len(violations) == 1
    assert violations[0].is_blocking
    assert "did not complete successfully" in violations[0].message


def test_violation_is_blocking_property():
    v_blocking = DependencyViolation("b", "a", 2, 1, "msg")
    v_none = DependencyViolation("b", "a", 2, None, "msg")
    assert v_blocking.is_blocking is True
    assert v_none.is_blocking is False


def test_all_violations_covers_all_jobs(store, graph):
    _add_run(store, "job_b")
    checker = RunDependencyChecker(store, graph)
    results = checker.all_violations(["job_a", "job_b"])
    assert "job_a" in results
    assert "job_b" in results
    assert results["job_a"] == []
    assert len(results["job_b"]) == 1


def test_graph_dependencies_unknown_job_returns_empty():
    g = DependencyGraph()
    assert g.dependencies("unknown") == []


def test_graph_add_multiple_deps():
    g = DependencyGraph()
    g.add("c", "a")
    g.add("c", "b")
    assert set(g.dependencies("c")) == {"a", "b"}
