"""Run ledger: tracks cumulative pass/fail counts per job across all time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class LedgerEntry:
    job_name: str
    total_runs: int
    total_successes: int
    total_failures: int
    first_run_at: Optional[str]  # ISO string or None
    last_run_at: Optional[str]

    @property
    def success_rate(self) -> Optional[float]:
        if self.total_runs == 0:
            return None
        return self.total_successes / self.total_runs

    @property
    def failure_rate(self) -> Optional[float]:
        if self.total_runs == 0:
            return None
        return self.total_failures / self.total_runs


class RunLedger:
    """Aggregates lifetime run statistics for each job from the store."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def entry(self, job_name: str) -> LedgerEntry:
        runs = self._store.get_runs(job_name)
        completed = [r for r in runs if r.end_time is not None]

        total_runs = len(completed)
        total_successes = sum(1 for r in completed if r.exit_code == 0)
        total_failures = total_runs - total_successes

        sorted_runs = sorted(completed, key=lambda r: r.start_time)
        first_run_at = sorted_runs[0].start_time if sorted_runs else None
        last_run_at = sorted_runs[-1].start_time if sorted_runs else None

        return LedgerEntry(
            job_name=job_name,
            total_runs=total_runs,
            total_successes=total_successes,
            total_failures=total_failures,
            first_run_at=first_run_at,
            last_run_at=last_run_at,
        )

    def all_entries(self, job_names: list[str]) -> list[LedgerEntry]:
        return [self.entry(name) for name in job_names]
