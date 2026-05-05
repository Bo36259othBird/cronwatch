"""Main daemon loop that ties together tracking, silence detection, and alerting."""

import logging
import signal
import time
from typing import Optional

from cronwatch.alerter import Alerter
from cronwatch.config import CronwatchConfig
from cronwatch.silence_detector import SilenceDetector
from cronwatch.store import JobStore
from cronwatch.tracker import JobTracker

logger = logging.getLogger(__name__)


class CronwatchDaemon:
    """Runs the main monitoring loop, checking for silent jobs and dispatching alerts."""

    def __init__(self, config: CronwatchConfig, poll_interval: int = 60) -> None:
        self.config = config
        self.poll_interval = poll_interval
        self.store = JobStore()
        self.tracker = JobTracker(self.store)
        self.alerter = Alerter(config)
        self.silence_detector = SilenceDetector(config, self.store)
        self._running = False
        self._alerted_silent: set[str] = set()

    def start(self) -> None:
        """Start the daemon loop, blocking until stopped."""
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        logger.info("cronwatch daemon started (poll_interval=%ds)", self.poll_interval)
        try:
            while self._running:
                self._tick()
                time.sleep(self.poll_interval)
        finally:
            logger.info("cronwatch daemon stopped")

    def stop(self) -> None:
        """Request a graceful shutdown."""
        self._running = False

    def _tick(self) -> None:
        """Single monitoring cycle: detect newly silent jobs and alert."""
        silent = self.silence_detector.silent_jobs()
        for job_name in silent:
            if job_name not in self._alerted_silent:
                last_run = self.store.get_last_run(job_name)
                self.alerter.alert_silence(job_name, last_run)
                self._alerted_silent.add(job_name)
                logger.warning("silence alert sent for job '%s'", job_name)
        # Clear alert state for jobs that have run again
        recovered = self._alerted_silent - set(silent)
        if recovered:
            logger.info("jobs recovered from silence: %s", recovered)
            self._alerted_silent -= recovered

    def _handle_signal(self, signum: int, frame: Optional[object]) -> None:  # noqa: ARG002
        logger.info("received signal %d, shutting down", signum)
        self.stop()
