"""Tests for RunDispatcher and dispatch_formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.store import JobRun
from cronwatch.run_dispatcher import DispatchEvent, RunDispatcher
from cronwatch.dispatch_formatter import format_event


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _run(exit_code: int = 0) -> JobRun:
    return JobRun(
        run_id=1,
        job_name="backup",
        started_at=_utc(2024, 1, 15, 3, 0, 0),
        finished_at=_utc(2024, 1, 15, 3, 5, 0),
        exit_code=exit_code,
    )


@pytest.fixture
def dispatcher() -> RunDispatcher:
    return RunDispatcher()


def test_register_and_dispatch_calls_handler(dispatcher):
    received = []
    dispatcher.register("started", received.append)
    run = _run()
    dispatcher.dispatch_started(run)
    assert len(received) == 1
    assert received[0].kind == "started"


def test_dispatch_finished_success_emits_finished(dispatcher):
    received = []
    dispatcher.register("finished", received.append)
    dispatcher.dispatch_finished(_run(exit_code=0))
    assert len(received) == 1
    assert received[0].kind == "finished"


def test_dispatch_finished_failure_emits_failed(dispatcher):
    received = []
    dispatcher.register("failed", received.append)
    dispatcher.dispatch_finished(_run(exit_code=1))
    assert len(received) == 1
    assert received[0].kind == "failed"


def test_unknown_kind_raises(dispatcher):
    with pytest.raises(ValueError, match="Unknown event kind"):
        dispatcher.register("unknown", lambda e: None)


def test_handler_count(dispatcher):
    assert dispatcher.handler_count("started") == 0
    dispatcher.register("started", lambda e: None)
    dispatcher.register("started", lambda e: None)
    assert dispatcher.handler_count("started") == 2


def test_multiple_handlers_all_called(dispatcher):
    calls = []
    dispatcher.register("finished", lambda e: calls.append("h1"))
    dispatcher.register("finished", lambda e: calls.append("h2"))
    dispatcher.dispatch_finished(_run(exit_code=0))
    assert calls == ["h1", "h2"]


def test_format_event_text_contains_job_name():
    event = DispatchEvent(kind="finished", job_name="backup", run_id=1, run=_run())
    text = format_event(event, fmt="text")
    assert "backup" in text


def test_format_event_text_contains_kind():
    event = DispatchEvent(kind="failed", job_name="backup", run_id=1, run=_run(exit_code=1))
    text = format_event(event, fmt="text")
    assert "FAILED" in text


def test_format_event_json_is_valid():
    event = DispatchEvent(kind="started", job_name="cleanup", run_id=7, run=_run())
    raw = format_event(event, fmt="json")
    data = json.loads(raw)
    assert data["job_name"] == "cleanup"
    assert data["run_id"] == 7


def test_format_event_json_kind_field():
    event = DispatchEvent(kind="started", job_name="cleanup", run_id=7, run=_run())
    data = json.loads(format_event(event, fmt="json"))
    assert data["kind"] == "started"
