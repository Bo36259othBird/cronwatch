"""Sentinel monitoring: detect jobs that have not run within their expected cadence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cronwatch.store import JobStore


@dataclass
class SentinelAlert:
    job_name: str
    expected_interval_seconds: float
    last_run_at: Optional[datetime]
    overdue_by_seconds: float

    @property
    def is_never_run(self) -> bool:
        return self.last_run_at is None

    @property
    def overdue_by_delta(self) -> timedelta:
        return timedelta(seconds=self.overdue_by_seconds)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class RunSentinel:
    """Checks whether jobs have run within an expected interval."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def check(self, job_name: str, interval_seconds: float) -> Optional[SentinelAlert]:
        """Return a SentinelAlert if the job is overdue, else None."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")

        last_run = self._store.get_last_run(job_name)
        now = _utcnow()

        if last_run is None:
            return SentinelAlert(
                job_name=job_name,
                expected_interval_seconds=interval_seconds,
                last_run_at=None,
                overdue_by_seconds=interval_seconds,
            )

        last_run_at = last_run.started_at
        if last_run_at.tzinfo is None:
            last_run_at = last_run_at.replace(tzinfo=timezone.utc)

        elapsed = (now - last_run_at).total_seconds()
        if elapsed > interval_seconds:
            return SentinelAlert(
                job_name=job_name,
                expected_interval_seconds=interval_seconds,
                last_run_at=last_run_at,
                overdue_by_seconds=elapsed - interval_seconds,
            )

        return None

    def check_all(self, intervals: dict[str, float]) -> List[SentinelAlert]:
        """Check multiple jobs. Returns only those that are overdue."""
        alerts: List[SentinelAlert] = []
        for job_name, interval in intervals.items():
            alert = self.check(job_name, interval)
            if alert is not None:
                alerts.append(alert)
        return alerts
