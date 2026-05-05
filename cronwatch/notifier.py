"""Email and log notification backend for cronwatch alerts."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from cronwatch.config import CronwatchConfig

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Raised when a notification cannot be delivered."""


class Notifier:
    """Sends notifications via SMTP and/or the logging subsystem."""

    def __init__(self, config: CronwatchConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, subject: str, body: str, *, job_name: Optional[str] = None) -> None:
        """Dispatch a notification through all configured channels."""
        self._log(subject, body, job_name=job_name)
        if self._smtp_enabled():
            self._send_email(subject, body)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, subject: str, body: str, *, job_name: Optional[str]) -> None:
        prefix = f"[{job_name}] " if job_name else ""
        logger.warning("%s%s — %s", prefix, subject, body)

    def _smtp_enabled(self) -> bool:
        smtp = getattr(self._config, "smtp", None)
        return smtp is not None and bool(getattr(smtp, "host", None))

    def _send_email(self, subject: str, body: str) -> None:
        smtp_cfg = self._config.smtp  # type: ignore[attr-defined]
        recipients = getattr(smtp_cfg, "recipients", [])
        if not recipients:
            logger.debug("SMTP configured but no recipients defined; skipping email.")
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = getattr(smtp_cfg, "sender", "cronwatch@localhost")
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)

        host = smtp_cfg.host
        port = getattr(smtp_cfg, "port", 25)
        try:
            with smtplib.SMTP(host, port, timeout=10) as server:
                username = getattr(smtp_cfg, "username", None)
                password = getattr(smtp_cfg, "password", None)
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
            logger.info("Alert email sent to %s", recipients)
        except (smtplib.SMTPException, OSError) as exc:
            raise NotificationError(f"Failed to send email: {exc}") from exc
