"""Compute per-job runtime statistics from historical runs."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median, stdev
from typing import List, Optional

from cronwatch.store import JobStore


@dataclass
class RunStats:
    """Aggregated duration statistics for a single job."""

    job_name: str
    run_count: int
    avg_duration: Optional[float]  # seconds
    median_duration: Optional[float]
    stddev_duration: Optional[float]
    min_duration: Optional[float]
    max_duration: Optional[float]

    def is_stable(self, threshold: float = 0.25) -> bool:
        """Return True when coefficient of variation is below *threshold*."""
        if self.avg_duration is None or self.avg_duration == 0:
            return True
        if self.stddev_duration is None:
            return True
        return (self.stddev_duration / self.avg_duration) < threshold


class RunStatsCollector:
    """Collect runtime statistics for jobs using a JobStore."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def collect(self, job_name: str, limit: int = 100) -> RunStats:
        """Return a :class:`RunStats` for *job_name* based on recent runs."""
        runs = self._store.get_runs(job_name, limit=limit)
        durations: List[float] = [
            r.duration_seconds
            for r in runs
            if r.duration_seconds is not None
        ]

        if not durations:
            return RunStats(
                job_name=job_name,
                run_count=len(runs),
                avg_duration=None,
                median_duration=None,
                stddev_duration=None,
                min_duration=None,
                max_duration=None,
            )

        return RunStats(
            job_name=job_name,
            run_count=len(runs),
            avg_duration=mean(durations),
            median_duration=median(durations),
            stddev_duration=stdev(durations) if len(durations) > 1 else 0.0,
            min_duration=min(durations),
            max_duration=max(durations),
        )
