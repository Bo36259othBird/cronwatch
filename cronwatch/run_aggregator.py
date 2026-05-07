"""Aggregate job run statistics across multiple jobs into a single summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.store import JobStore


@dataclass
class JobAggregate:
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
class AggregateReport:
    aggregates: List[JobAggregate] = field(default_factory=list)

    @property
    def total_jobs(self) -> int:
        return len(self.aggregates)

    @property
    def total_runs(self) -> int:
        return sum(a.total_runs for a in self.aggregates)

    @property
    def total_failures(self) -> int:
        return sum(a.failed_runs for a in self.aggregates)

    def by_name(self, name: str) -> Optional[JobAggregate]:
        return next((a for a in self.aggregates if a.job_name == name), None)


class RunAggregator:
    def __init__(self, store: JobStore) -> None:
        self._store = store

    def aggregate(self, job_names: List[str]) -> AggregateReport:
        aggregates: List[JobAggregate] = []
        for name in job_names:
            runs = self._store.get_runs(name)
            total = len(runs)
            successful = sum(1 for r in runs if r.exit_code == 0)
            failed = sum(1 for r in runs if r.exit_code != 0 and r.exit_code is not None)
            durations = [
                r.duration_seconds
                for r in runs
                if r.duration_seconds is not None
            ]
            avg_dur = sum(durations) / len(durations) if durations else None
            max_dur = max(durations) if durations else None
            min_dur = min(durations) if durations else None
            aggregates.append(
                JobAggregate(
                    job_name=name,
                    total_runs=total,
                    successful_runs=successful,
                    failed_runs=failed,
                    avg_duration_seconds=avg_dur,
                    max_duration_seconds=max_dur,
                    min_duration_seconds=min_dur,
                )
            )
        return AggregateReport(aggregates=aggregates)
