"""High-level job lifecycle tracker that ties the store to alerting."""

import logging
from typing import Dict, Optional

from cronwatch.store import JobStore, JobRun

logger = logging.getLogger(__name__)


class JobTracker:
    """Tracks in-progress and completed job runs."""

    def __init__(self, store: Optional[JobStore] = None) -> None:
        self.store = store or JobStore()
        self._active: Dict[str, int] = {}  # job_name -> run_id

    def start(self, job_name: str) -> int:
        """Signal that a job has started. Returns the run_id."""
        if job_name in self._active:
            logger.warning(
                "Job '%s' started while a previous run (id=%d) is still active.",
                job_name,
                self._active[job_name],
            )
        run_id = self.store.record_start(job_name)
        self._active[job_name] = run_id
        logger.info("Job '%s' started (run_id=%d).", job_name, run_id)
        return run_id

    def finish(self, job_name: str, exit_code: int) -> Optional[JobRun]:
        """Signal that a job has finished. Returns the completed JobRun."""
        run_id = self._active.pop(job_name, None)
        if run_id is None:
            logger.error(
                "Received finish for unknown job '%s' — no active run found.",
                job_name,
            )
            return None
        self.store.record_finish(run_id, exit_code)
        run = self.store.get_last_run(job_name)
        status = "succeeded" if exit_code == 0 else f"failed (exit={exit_code})"
        logger.info(
            "Job '%s' %s in %.2fs (run_id=%d).",
            job_name,
            status,
            run.duration or 0.0,
            run_id,
        )
        return run

    def is_active(self, job_name: str) -> bool:
        return job_name in self._active

    def active_jobs(self):
        return list(self._active.keys())

    def last_run(self, job_name: str) -> Optional[JobRun]:
        return self.store.get_last_run(job_name)
