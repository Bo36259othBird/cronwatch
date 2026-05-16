"""Pin notable runs (e.g. slowest, fastest, first failure) for quick reference."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class PinnedRun:
    job_name: str
    run_id: int
    reason: str  # e.g. "slowest", "fastest", "first_failure"
    duration: Optional[float]  # seconds, None if incomplete

    def is_failure(self) -> bool:
        return self.reason == "first_failure"


class RunPinner:
    """Identify and return pinned (notable) runs for a given job."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def _completed(self, job_name: str) -> list[JobRun]:
        runs = self._store.get_runs(job_name)
        return [r for r in runs if r.end_time is not None]

    def slowest(self, job_name: str) -> Optional[PinnedRun]:
        completed = self._completed(job_name)
        if not completed:
            return None
        run = max(completed, key=lambda r: (r.end_time - r.start_time).total_seconds())
        duration = (run.end_time - run.start_time).total_seconds()
        return PinnedRun(job_name=job_name, run_id=run.id, reason="slowest", duration=duration)

    def fastest(self, job_name: str) -> Optional[PinnedRun]:
        completed = self._completed(job_name)
        if not completed:
            return None
        run = min(completed, key=lambda r: (r.end_time - r.start_time).total_seconds())
        duration = (run.end_time - run.start_time).total_seconds()
        return PinnedRun(job_name=job_name, run_id=run.id, reason="fastest", duration=duration)

    def first_failure(self, job_name: str) -> Optional[PinnedRun]:
        runs = self._store.get_runs(job_name)
        failures = [r for r in runs if r.exit_code not in (None, 0)]
        if not failures:
            return None
        run = failures[0]
        duration = (
            (run.end_time - run.start_time).total_seconds()
            if run.end_time is not None
            else None
        )
        return PinnedRun(job_name=job_name, run_id=run.id, reason="first_failure", duration=duration)

    def all_pins(self, job_name: str) -> list[PinnedRun]:
        pins = [
            self.slowest(job_name),
            self.fastest(job_name),
            self.first_failure(job_name),
        ]
        return [p for p in pins if p is not None]
