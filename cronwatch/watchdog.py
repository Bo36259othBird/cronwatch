"""Watchdog module: detects jobs that have exceeded their expected max duration."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from cronwatch.config import CronwatchConfig
from cronwatch.store import JobStore


@dataclass
class OverdueRun:
    job_name: str
    run_id: int
    started_at: datetime
    elapsed_seconds: float
    max_duration_seconds: int


class Watchdog:
    """Checks for in-progress job runs that have exceeded their configured max duration."""

    def __init__(self, config: CronwatchConfig, store: JobStore) -> None:
        self._config = config
        self._store = store
        self._alerted: set = set()

    def overdue_runs(self) -> List[OverdueRun]:
        """Return a list of active runs that have exceeded max_duration_seconds."""
        now = datetime.now(timezone.utc)
        results: List[OverdueRun] = []

        for job in self._config.jobs:
            if job.max_duration_seconds is None:
                continue

            run = self._store.get_last_run(job.name)
            if run is None:
                continue

            # Only consider incomplete (still running) jobs
            if run.finished_at is not None:
                continue

            started = run.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)

            elapsed = (now - started).total_seconds()
            if elapsed > job.max_duration_seconds:
                results.append(
                    OverdueRun(
                        job_name=job.name,
                        run_id=run.run_id,
                        started_at=started,
                        elapsed_seconds=elapsed,
                        max_duration_seconds=job.max_duration_seconds,
                    )
                )

        return results

    def new_overdue_runs(self) -> List[OverdueRun]:
        """Return overdue runs not yet alerted, and mark them as alerted."""
        overdue = self.overdue_runs()
        new = [r for r in overdue if r.run_id not in self._alerted]
        for r in new:
            self._alerted.add(r.run_id)
        return new

    def clear_alerted(self, run_id: int) -> None:
        """Remove a run from the alerted set (e.g. after it completes)."""
        self._alerted.discard(run_id)
