"""Job run history queries and trend analysis."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class JobTrend:
    job_name: str
    window_days: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_duration_seconds: Optional[float]
    last_run_at: Optional[datetime]

    @property
    def failure_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.failed_runs / self.total_runs

    @property
    def is_degrading(self) -> bool:
        """True when failure rate exceeds 25 %."""
        return self.failure_rate > 0.25


class HistoryAnalyzer:
    """Compute trends from stored job runs."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def trend(self, job_name: str, window_days: int = 7) -> JobTrend:
        cutoff = datetime.utcnow() - timedelta(days=window_days)
        runs: List[JobRun] = [
            r for r in self._store.get_runs(job_name)
            if r.started_at >= cutoff
        ]

        successful = [r for r in runs if r.exit_code == 0]
        failed = [r for r in runs if r.exit_code is not None and r.exit_code != 0]

        durations = [
            (r.finished_at - r.started_at).total_seconds()
            for r in runs
            if r.finished_at is not None
        ]
        avg_dur = sum(durations) / len(durations) if durations else None
        last_run = max((r.started_at for r in runs), default=None)

        return JobTrend(
            job_name=job_name,
            window_days=window_days,
            total_runs=len(runs),
            successful_runs=len(successful),
            failed_runs=len(failed),
            avg_duration_seconds=avg_dur,
            last_run_at=last_run,
        )

    def all_trends(self, job_names: List[str], window_days: int = 7) -> List[JobTrend]:
        return [self.trend(name, window_days) for name in job_names]
