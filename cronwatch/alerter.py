"""Alerter module: sends notifications on job failures or silence."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import List, Optional

from cronwatch.config import CronwatchConfig
from cronwatch.store import JobRun

logger = logging.getLogger(__name__)


@dataclass
class AlertEvent:
    """Represents a single alert event."""

    job_name: str
    kind: str  # "failure" | "silence" | "timeout"
    message: str
    run: Optional[JobRun] = None


class Alerter:
    """Sends alert notifications based on job events."""

    def __init__(self, config: CronwatchConfig) -> None:
        self._config = config
        self._sent: List[AlertEvent] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def alert_failure(self, job_name: str, run: JobRun) -> None:
        """Send an alert for a failed job run."""
        event = AlertEvent(
            job_name=job_name,
            kind="failure",
            message=f"Job '{job_name}' failed (exit code {run.exit_code}).",
            run=run,
        )
        self._dispatch(event)

    def alert_silence(self, job_name: str) -> None:
        """Send an alert when a job has been unexpectedly silent."""
        event = AlertEvent(
            job_name=job_name,
            kind="silence",
            message=f"Job '{job_name}' has not run within the expected window.",
        )
        self._dispatch(event)

    def alert_timeout(self, job_name: str, run: JobRun) -> None:
        """Send an alert when a job has exceeded its max duration."""
        event = AlertEvent(
            job_name=job_name,
            kind="timeout",
            message=f"Job '{job_name}' exceeded its maximum allowed duration.",
            run=run,
        )
        self._dispatch(event)

    @property
    def sent_events(self) -> List[AlertEvent]:
        """Return a copy of all dispatched events (useful for testing)."""
        return list(self._sent)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dispatch(self, event: AlertEvent) -> None:
        logger.warning("[cronwatch] ALERT [%s] %s", event.kind.upper(), event.message)
        self._sent.append(event)
        if self._config.smtp:
            self._send_email(event)

    def _send_email(self, event: AlertEvent) -> None:
        smtp_cfg = self._config.smtp
        msg = EmailMessage()
        msg["Subject"] = f"[cronwatch] {event.kind.upper()}: {event.job_name}"
        msg["From"] = smtp_cfg.get("from", "cronwatch@localhost")
        msg["To"] = smtp_cfg.get("to", "")
        msg.set_content(event.message)
        try:
            with smtplib.SMTP(smtp_cfg.get("host", "localhost"), smtp_cfg.get("port", 25)) as s:
                s.send_message(msg)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to send alert email: %s", exc)
