"""Tests for cronwatch.notifier."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifier import NotificationError, Notifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config(smtp=None):
    """Build a minimal CronwatchConfig-like object."""
    return SimpleNamespace(smtp=smtp)


def _smtp_cfg(**kwargs):
    defaults = dict(host="localhost", port=25, sender="cw@localhost", recipients=["ops@example.com"])
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def notifier_no_smtp():
    return Notifier(_config(smtp=None))


@pytest.fixture()
def notifier_with_smtp():
    return Notifier(_config(smtp=_smtp_cfg()))


# ---------------------------------------------------------------------------
# Tests — logging channel
# ---------------------------------------------------------------------------

def test_send_logs_warning(notifier_no_smtp, caplog):
    with caplog.at_level(logging.WARNING, logger="cronwatch.notifier"):
        notifier_no_smtp.send("Test subject", "Test body")
    assert "Test subject" in caplog.text


def test_send_includes_job_name_in_log(notifier_no_smtp, caplog):
    with caplog.at_level(logging.WARNING, logger="cronwatch.notifier"):
        notifier_no_smtp.send("Failure", "exit code 1", job_name="backup")
    assert "[backup]" in caplog.text


def test_send_no_job_name_no_bracket(notifier_no_smtp, caplog):
    with caplog.at_level(logging.WARNING, logger="cronwatch.notifier"):
        notifier_no_smtp.send("Silence", "no runs detected")
    assert "[" not in caplog.text


# ---------------------------------------------------------------------------
# Tests — SMTP channel
# ---------------------------------------------------------------------------

def test_send_calls_smtp_when_configured(notifier_with_smtp):
    with patch("cronwatch.notifier.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        notifier_with_smtp.send("Alert", "something went wrong")
    mock_smtp_cls.assert_called_once_with("localhost", 25, timeout=10)
    mock_server.send_message.assert_called_once()


def test_send_no_smtp_when_not_configured(notifier_no_smtp):
    with patch("cronwatch.notifier.smtplib.SMTP") as mock_smtp_cls:
        notifier_no_smtp.send("Alert", "body")
    mock_smtp_cls.assert_not_called()


def test_smtp_error_raises_notification_error():
    import smtplib
    notifier = Notifier(_config(smtp=_smtp_cfg()))
    with patch("cronwatch.notifier.smtplib.SMTP", side_effect=smtplib.SMTPException("conn refused")):
        with pytest.raises(NotificationError, match="conn refused"):
            notifier.send("Subject", "Body")


def test_no_recipients_skips_smtp(caplog):
    notifier = Notifier(_config(smtp=_smtp_cfg(recipients=[])))
    with patch("cronwatch.notifier.smtplib.SMTP") as mock_smtp_cls:
        with caplog.at_level(logging.DEBUG, logger="cronwatch.notifier"):
            notifier.send("Subject", "Body")
    mock_smtp_cls.assert_not_called()
    assert "no recipients" in caplog.text
