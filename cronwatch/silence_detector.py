"""Detect jobs that have not run within their expected schedule window."""

import time
import logging
from typing import List

from cronwatch.config import JobConfig
from cronwatch.store import JobStore, JobRun

logger = logging.getLogger(__name__)


class SilenceDetector:
    """Checks whether jobs have been silent longer than their allowed window."""

    def __init__(self, store: JobStore) -> None:
        self.store = store

    def is_silent(self, job: JobConfig) -> bool:
        """Return True if the job has exceeded its silence_threshold."""
        if job.silence_threshold is None:
            return False
        last = self.store.get_last_run(job.name)
        if last is None:
            # Never ran — treat as silent only if threshold is set
            logger.debug("Job '%s' has never run.", job.name)
            return True
        elapsed = time.time() - last.started_at
        silent = elapsed > job.silence_threshold
        if silent:
            logger.warning(
                "Job '%s' is silent: last run %.0fs ago, threshold=%ds.",
                job.name,
                elapsed,
                job.silence_threshold,
            )
        return silent

    def silent_jobs(self, jobs: List[JobConfig]) -> List[JobConfig]:
        """Return the subset of jobs that are currently silent."""
        return [j for j in jobs if self.is_silent(j)]
