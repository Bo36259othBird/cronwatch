"""Summarize runs for a job over a given time window."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class RunSummary:
    job_name: str
    window_hours: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_duration_seconds: Optional[float]
    min_duration_seconds: Optional[float]
    max_duration_seconds: Optional[float]

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    @property
    def failure_rate(self) -> float:
        return 1.0 - self.success_rate


class RunSummarizer:
    def __init__(self, store: JobStore) -> None:
        self._store = store

    def summarize(self, job_name: str, window_hours: int = 24) -> RunSummary:
        since = datetime.now(tz=timezone.utc) - timedelta(hours=window_hours)
        runs = [
            r
            for r in self._store.get_runs(job_name)
            if r.started_at >= since
        ]

        total = len(runs)
        successful = sum(1 for r in runs if r.exit_code == 0)
        failed = sum(1 for r in runs if r.exit_code is not None and r.exit_code != 0)

        durations = [
            (r.finished_at - r.started_at).total_seconds()
            for r in runs
            if r.finished_at is not None
        ]

        avg_dur = sum(durations) / len(durations) if durations else None
        min_dur = min(durations) if durations else None
        max_dur = max(durations) if durations else None

        return RunSummary(
            job_name=job_name,
            window_hours=window_hours,
            total_runs=total,
            successful_runs=successful,
            failed_runs=failed,
            avg_duration_seconds=avg_dur,
            min_duration_seconds=min_dur,
            max_duration_seconds=max_dur,
        )
