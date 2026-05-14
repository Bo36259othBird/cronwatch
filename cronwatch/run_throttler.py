"""Throttle-based run rate analysis: detects jobs running too frequently."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cronwatch.store import JobStore


@dataclass
class ThrottleViolation:
    job_name: str
    run_id: int
    started_at: datetime
    previous_started_at: datetime
    gap_seconds: float
    min_gap_seconds: float

    @property
    def is_violation(self) -> bool:
        return self.gap_seconds < self.min_gap_seconds

    @property
    def gap_delta(self) -> timedelta:
        return timedelta(seconds=self.gap_seconds)


class RunThrottler:
    """Detects runs that started sooner than a configured minimum interval."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def check(self, job_name: str, min_gap_seconds: float, limit: int = 50) -> List[ThrottleViolation]:
        """Return violations where consecutive runs started too close together."""
        runs = self._store.get_runs(job_name, limit=limit)
        if len(runs) < 2:
            return []

        # Sort ascending by start time
        runs = sorted(runs, key=lambda r: r.started_at)

        violations: List[ThrottleViolation] = []
        for prev, curr in zip(runs, runs[1:]):
            if prev.started_at is None or curr.started_at is None:
                continue
            gap = (curr.started_at - prev.started_at).total_seconds()
            if gap < min_gap_seconds:
                violations.append(
                    ThrottleViolation(
                        job_name=job_name,
                        run_id=curr.run_id,
                        started_at=curr.started_at,
                        previous_started_at=prev.started_at,
                        gap_seconds=gap,
                        min_gap_seconds=min_gap_seconds,
                    )
                )
        return violations

    def any_violations(self, job_name: str, min_gap_seconds: float) -> bool:
        return len(self.check(job_name, min_gap_seconds)) > 0
