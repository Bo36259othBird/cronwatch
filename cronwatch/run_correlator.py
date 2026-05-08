"""Correlate runs across jobs to find timing relationships and co-failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class CorrelatedPair:
    job_a: str
    job_b: str
    overlap_count: int
    co_failure_count: int

    @property
    def co_failure_rate(self) -> float:
        if self.overlap_count == 0:
            return 0.0
        return self.co_failure_count / self.overlap_count

    @property
    def is_correlated(self) -> bool:
        """True when co-failure rate exceeds 50%."""
        return self.co_failure_rate >= 0.5


def _runs_overlap(a: JobRun, b: JobRun, window: timedelta) -> bool:
    """Return True if the two runs started within *window* of each other."""
    if a.started_at is None or b.started_at is None:
        return False
    return abs(a.started_at - b.started_at) <= window


def _is_failure(run: JobRun) -> bool:
    return run.exit_code is not None and run.exit_code != 0


class RunCorrelator:
    """Find jobs that tend to fail together within a time window."""

    def __init__(self, store: JobStore, window_seconds: int = 60) -> None:
        self._store = store
        self._window = timedelta(seconds=window_seconds)

    def correlate(self, job_a: str, job_b: str) -> CorrelatedPair:
        runs_a = self._store.get_runs(job_a)
        runs_b = self._store.get_runs(job_b)

        overlap = 0
        co_failures = 0

        for ra in runs_a:
            for rb in runs_b:
                if _runs_overlap(ra, rb, self._window):
                    overlap += 1
                    if _is_failure(ra) and _is_failure(rb):
                        co_failures += 1

        return CorrelatedPair(
            job_a=job_a,
            job_b=job_b,
            overlap_count=overlap,
            co_failure_count=co_failures,
        )

    def correlate_all(self, job_names: List[str]) -> List[CorrelatedPair]:
        """Return correlation pairs for every unique combination of jobs."""
        pairs: List[CorrelatedPair] = []
        names = list(job_names)
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                pairs.append(self.correlate(a, b))
        return pairs
