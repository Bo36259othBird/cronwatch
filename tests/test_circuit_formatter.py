"""Tests for circuit_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.run_circuit_breaker import CircuitState
from cronwatch.circuit_formatter import format_circuits


def _state(
    job_name="backup",
    is_open=True,
    failure_count=3,
    total_count=4,
    threshold=0.5,
    tripped_at=None,
):
    return CircuitState(
        job_name=job_name,
        is_open=is_open,
        failure_count=failure_count,
        total_count=total_count,
        tripped_at=tripped_at,
        threshold=threshold,
    )


def test_text_contains_job_name():
    out = format_circuits([_state(job_name="my_job")])
    assert "my_job" in out


def test_text_contains_header():
    out = format_circuits([_state()])
    assert "Circuit Breaker" in out


def test_text_shows_open_status():
    out = format_circuits([_state(is_open=True)])
    assert "OPEN" in out


def test_text_shows_closed_status():
    out = format_circuits([_state(is_open=False, failure_count=0)])
    assert "closed" in out


def test_text_shows_tripped_at_when_set():
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    out = format_circuits([_state(tripped_at=ts)])
    assert "tripped at" in out
    assert "2024-06-01" in out


def test_text_empty_list():
    out = format_circuits([])
    assert "No circuit data" in out


def test_json_format_is_valid():
    out = format_circuits([_state()], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1


def test_json_contains_expected_keys():
    out = format_circuits([_state()], fmt="json")
    data = json.loads(out)
    keys = data[0].keys()
    assert "job_name" in keys
    assert "is_open" in keys
    assert "failure_rate" in keys
    assert "threshold" in keys


def test_json_failure_rate_rounded():
    out = format_circuits([_state(failure_count=1, total_count=3)], fmt="json")
    data = json.loads(out)
    assert data[0]["failure_rate"] == pytest.approx(0.3333, abs=1e-3)
