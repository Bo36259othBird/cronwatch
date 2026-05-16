"""Run quota enforcement — limits how many runs a job may record in a time window."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class QuotaResult:
    job_name: str
    window_seconds: int
    limit: int
    actual: int
    exceeded: bool
    excess: int

    @property
    def utilisation(self) -> float:
        """Fraction of quota used (may exceed 1.0)."""
        if self.limit == 0:
            return 0.0
        return self.actual / self.limit


def is_exceeded(result: QuotaResult) -> bool:
    return result.exceeded


class RunQuotaChecker:
    """Check whether a job has exceeded its allowed run count within a rolling window."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def check(
        self,
        job_name: str,
        limit: int,
        window_seconds: int,
        reference: Optional[datetime] = None,
    ) -> QuotaResult:
        """Return a QuotaResult for *job_name* over the most recent *window_seconds*."""
        if reference is None:
            reference = datetime.now(tz=timezone.utc)

        cutoff = reference - timedelta(seconds=window_seconds)
        runs = self._store.get_runs(job_name)
        in_window = [
            r
            for r in runs
            if r.started_at >= cutoff
        ]
        actual = len(in_window)
        exceeded = actual > limit
        excess = max(0, actual - limit)
        return QuotaResult(
            job_name=job_name,
            window_seconds=window_seconds,
            limit=limit,
            actual=actual,
            exceeded=exceeded,
            excess=excess,
        )
