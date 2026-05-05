"""Tests for cronwatch.alerter."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerter import Alerter, AlertEvent
from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.store import JobRun


def _make_run(exit_code: int = 1) -> JobRun:
    return JobRun(
        id=1,
        job_name="test_job",
        started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        finished_at=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        exit_code=exit_code,
        duration=60.0,
    )


@pytest.fixture
def config_no_smtp() -> CronwatchConfig:
    return CronwatchConfig(
        jobs=[JobConfig(name="test_job", schedule="* * * * *")],
        smtp=None,
    )


@pytest.fixture
def config_with_smtp() -> CronwatchConfig:
    return CronwatchConfig(
        jobs=[JobConfig(name="test_job", schedule="* * * * *")],
        smtp={"host": "localhost", "port": 25, "from": "cw@local", "to": "admin@local"},
    )


@pytest.fixture
def alerter(config_no_smtp: CronwatchConfig) -> Alerter:
    return Alerter(config_no_smtp)


def test_alert_failure_records_event(alerter: Alerter) -> None:
    run = _make_run(exit_code=2)
    alerter.alert_failure("test_job", run)
    assert len(alerter.sent_events) == 1
    event = alerter.sent_events[0]
    assert event.kind == "failure"
    assert event.job_name == "test_job"
    assert "failed" in event.message


def test_alert_silence_records_event(alerter: Alerter) -> None:
    alerter.alert_silence("test_job")
    assert len(alerter.sent_events) == 1
    event = alerter.sent_events[0]
    assert event.kind == "silence"
    assert "silent" in event.message.lower() or "not run" in event.message.lower()


def test_alert_timeout_records_event(alerter: Alerter) -> None:
    run = _make_run(exit_code=0)
    alerter.alert_timeout("test_job", run)
    assert len(alerter.sent_events) == 1
    event = alerter.sent_events[0]
    assert event.kind == "timeout"


def test_multiple_alerts_accumulate(alerter: Alerter) -> None:
    alerter.alert_silence("job_a")
    alerter.alert_silence("job_b")
    alerter.alert_failure("job_a", _make_run())
    assert len(alerter.sent_events) == 3


def test_sent_events_returns_copy(alerter: Alerter) -> None:
    alerter.alert_silence("job_a")
    events = alerter.sent_events
    events.clear()
    assert len(alerter.sent_events) == 1


def test_smtp_send_called_when_configured(config_with_smtp: CronwatchConfig) -> None:
    alerter = Alerter(config_with_smtp)
    with patch("cronwatch.alerter.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        alerter.alert_silence("test_job")
    mock_smtp_cls.assert_called_once_with("localhost", 25)


def test_no_smtp_call_without_config(config_no_smtp: CronwatchConfig) -> None:
    alerter = Alerter(config_no_smtp)
    with patch("cronwatch.alerter.smtplib.SMTP") as mock_smtp_cls:
        alerter.alert_silence("test_job")
    mock_smtp_cls.assert_not_called()
