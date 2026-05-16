"""Tests for dependency_formatter."""
from __future__ import annotations

import json

import pytest

from cronwatch.run_dependency import DependencyViolation
from cronwatch.dependency_formatter import format_dependencies


def _violation(job="job_b", dep="job_a", run_id=2, blocking=1):
    return DependencyViolation(
        job_name=job,
        depends_on=dep,
        last_dependent_run_id=run_id,
        blocking_run_id=blocking,
        message=f"Dependency '{dep}' last run did not complete successfully.",
    )


def test_text_contains_header():
    result = format_dependencies({}, fmt="text")
    assert "Dependency Violations" in result


def test_text_no_violations_shows_none_detected():
    result = format_dependencies({"job_b": []}, fmt="text")
    assert "No violations detected" in result


def test_text_contains_job_name():
    v = _violation()
    result = format_dependencies({"job_b": [v]}, fmt="text")
    assert "job_b" in result


def test_text_contains_depends_on():
    v = _violation()
    result = format_dependencies({"job_b": [v]}, fmt="text")
    assert "job_a" in result


def test_text_shows_blocking_run_id():
    v = _violation(blocking=42)
    result = format_dependencies({"job_b": [v]}, fmt="text")
    assert "42" in result


def test_json_format_is_valid_json():
    v = _violation()
    result = format_dependencies({"job_b": [v]}, fmt="json")
    parsed = json.loads(result)
    assert "job_b" in parsed


def test_json_violation_fields():
    v = _violation()
    result = format_dependencies({"job_b": [v]}, fmt="json")
    parsed = json.loads(result)
    entry = parsed["job_b"][0]
    assert entry["depends_on"] == "job_a"
    assert entry["is_blocking"] is True
    assert entry["blocking_run_id"] == 1


def test_json_empty_violations():
    result = format_dependencies({"job_a": []}, fmt="json")
    parsed = json.loads(result)
    assert parsed["job_a"] == []
