"""Tests for CronwatchDaemon tick logic and silence alerting behaviour."""

from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.daemon import CronwatchDaemon


@pytest.fixture()
def config() -> CronwatchConfig:
    return CronwatchConfig(
        jobs=[
            JobConfig(name="backup", schedule="0 2 * * *", silence_threshold=3600),
            JobConfig(name="report", schedule="0 6 * * *", silence_threshold=7200),
        ],
        smtp=None,
        alert_email=None,
    )


@pytest.fixture()
def daemon(config: CronwatchConfig) -> CronwatchDaemon:
    d = CronwatchDaemon(config, poll_interval=1)
    return d


def test_tick_sends_alert_for_silent_job(daemon: CronwatchDaemon) -> None:
    daemon.silence_detector.silent_jobs = MagicMock(return_value=["backup"])
    daemon.store.get_last_run = MagicMock(return_value=None)
    daemon.alerter.alert_silence = MagicMock()

    daemon._tick()

    daemon.alerter.alert_silence.assert_called_once_with("backup", None)
    assert "backup" in daemon._alerted_silent


def test_tick_does_not_double_alert(daemon: CronwatchDaemon) -> None:
    daemon.silence_detector.silent_jobs = MagicMock(return_value=["backup"])
    daemon.store.get_last_run = MagicMock(return_value=None)
    daemon.alerter.alert_silence = MagicMock()

    daemon._tick()
    daemon._tick()

    assert daemon.alerter.alert_silence.call_count == 1


def test_tick_clears_alert_state_on_recovery(daemon: CronwatchDaemon) -> None:
    daemon._alerted_silent = {"backup"}
    daemon.silence_detector.silent_jobs = MagicMock(return_value=[])
    daemon.alerter.alert_silence = MagicMock()

    daemon._tick()

    assert "backup" not in daemon._alerted_silent
    daemon.alerter.alert_silence.assert_not_called()


def test_tick_no_alert_when_no_silent_jobs(daemon: CronwatchDaemon) -> None:
    daemon.silence_detector.silent_jobs = MagicMock(return_value=[])
    daemon.alerter.alert_silence = MagicMock()

    daemon._tick()

    daemon.alerter.alert_silence.assert_not_called()
    assert len(daemon._alerted_silent) == 0


def test_stop_sets_running_false(daemon: CronwatchDaemon) -> None:
    daemon._running = True
    daemon.stop()
    assert daemon._running is False


def test_start_calls_tick_and_stops(daemon: CronwatchDaemon) -> None:
    call_count = 0

    def fake_tick() -> None:
        nonlocal call_count
        call_count += 1
        daemon.stop()

    daemon._tick = fake_tick  # type: ignore[method-assign]

    with patch("time.sleep"):
        daemon.start()

    assert call_count == 1
    assert daemon._running is False
