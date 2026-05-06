"""Collect and expose runtime metrics for cronwatch jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.store import JobStore


@dataclass
class JobMetrics:
    job_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_duration_seconds: Optional[float]
    max_duration_seconds: Optional[float]
    min_duration_seconds: Optional[float]

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs


@dataclass
class MetricsReport:
    jobs: List[JobMetrics] = field(default_factory=list)

    def by_name(self, name: str) -> Optional[JobMetrics]:
        for j in self.jobs:
            if j.job_name == name:
                return j
        return None


class MetricsCollector:
    """Compute per-job runtime metrics from the job store."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def collect(self, job_names: List[str]) -> MetricsReport:
        report = MetricsReport()
        for name in job_names:
            runs = self._store.get_runs(name)
            complete = [r for r in runs if r.end_time is not None]
            successful = [r for r in complete if r.exit_code == 0]
            failed = [r for r in complete if r.exit_code != 0]

            durations: List[float] = []
            for r in complete:
                if r.start_time and r.end_time:
                    durations.append((r.end_time - r.start_time).total_seconds())

            report.jobs.append(
                JobMetrics(
                    job_name=name,
                    total_runs=len(complete),
                    successful_runs=len(successful),
                    failed_runs=len(failed),
                    avg_duration_seconds=(
                        sum(durations) / len(durations) if durations else None
                    ),
                    max_duration_seconds=max(durations) if durations else None,
                    min_duration_seconds=min(durations) if durations else None,
                )
            )
        return report
