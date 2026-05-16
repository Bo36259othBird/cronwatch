"""run_fence.py – enforce concurrency limits per job.

A 'fence' prevents a job from having more than N active (started but not
finished) runs at the same time.  Useful for catching runaway cron jobs
that overlap with themselves.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronwatch.store import JobStore


@dataclass
class FenceViolation:
    job_name: str
    active_count: int
    limit: int

    @property
    def excess(self) -> int:
        """Number of runs above the allowed limit."""
        return self.active_count - self.limit

    @property
    def is_violation(self) -> bool:
        return self.active_count > self.limit


class RunFence:
    """Check whether any job exceeds its concurrency limit."""

    def __init__(self, store: JobStore, default_limit: int = 1) -> None:
        if default_limit < 1:
            raise ValueError("default_limit must be >= 1")
        self._store = store
        self._default_limit = default_limit
        # per-job overrides: job_name -> limit
        self._limits: dict[str, int] = {}

    def set_limit(self, job_name: str, limit: int) -> None:
        """Override the concurrency limit for a specific job."""
        if limit < 1:
            raise ValueError("limit must be >= 1")
        self._limits[job_name] = limit

    def _limit_for(self, job_name: str) -> int:
        return self._limits.get(job_name, self._default_limit)

    def check(self, job_name: str) -> FenceViolation:
        """Return a FenceViolation describing the current state for *job_name*."""
        runs = self._store.get_runs(job_name)
        active = [r for r in runs if not r.end_time]
        limit = self._limit_for(job_name)
        return FenceViolation(
            job_name=job_name,
            active_count=len(active),
            limit=limit,
        )

    def violations(self, job_names: List[str]) -> List[FenceViolation]:
        """Return FenceViolation objects only for jobs that exceed their limit."""
        result = []
        for name in job_names:
            v = self.check(name)
            if v.is_violation:
                result.append(v)
        return result
