"""Generates summary reports of cron job execution history."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class JobSummary:
    job_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_duration_seconds: Optional[float]
    last_run_at: Optional[datetime]
    last_exit_code: Optional[int]

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs * 100


@dataclass
class Report:
    generated_at: datetime
    period_hours: int
    summaries: List[JobSummary]

    @property
    def total_failures(self) -> int:
        return sum(s.failed_runs for s in self.summaries)


class Reporter:
    def __init__(self, store: JobStore):
        self._store = store

    def generate(self, job_names: List[str], period_hours: int = 24) -> Report:
        since = datetime.utcnow() - timedelta(hours=period_hours)
        summaries = []
        for name in job_names:
            runs = self._store.get_runs_since(name, since)
            summaries.append(self._summarise(name, runs))
        return Report(
            generated_at=datetime.utcnow(),
            period_hours=period_hours,
            summaries=summaries,
        )

    def _summarise(self, job_name: str, runs: List[JobRun]) -> JobSummary:
        complete = [r for r in runs if r.finished_at is not None]
        successful = [r for r in complete if r.exit_code == 0]
        failed = [r for r in complete if r.exit_code != 0]

        durations = [
            (r.finished_at - r.started_at).total_seconds()
            for r in complete
            if r.finished_at and r.started_at
        ]
        avg_duration = sum(durations) / len(durations) if durations else None

        last_run = max((r.started_at for r in runs), default=None)
        last_exit = complete[-1].exit_code if complete else None

        return JobSummary(
            job_name=job_name,
            total_runs=len(runs),
            successful_runs=len(successful),
            failed_runs=len(failed),
            avg_duration_seconds=avg_duration,
            last_run_at=last_run,
            last_exit_code=last_exit,
        )
