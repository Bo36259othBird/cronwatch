"""Predict next expected run times and flag overdue schedules."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cronwatch.config import JobConfig
from cronwatch.scheduler import ScheduleChecker
from cronwatch.store import JobStore


@dataclass
class RunPlan:
    job_name: str
    last_run: Optional[datetime]
    next_expected: Optional[datetime]
    is_overdue: bool
    seconds_until_due: Optional[float]

    def is_imminent(self, window_seconds: float = 60.0) -> bool:
        """Return True if the next run is due within *window_seconds*."""
        if self.seconds_until_due is None:
            return False
        return 0 < self.seconds_until_due <= window_seconds


class RunPlanner:
    """Build a :class:`RunPlan` for each configured job."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def plan(self, job: JobConfig, now: Optional[datetime] = None) -> RunPlan:
        """Return a :class:`RunPlan` for *job* evaluated at *now*."""
        if now is None:
            now = datetime.now(timezone.utc)

        checker = ScheduleChecker(job)
        last_run_record = self._store.get_last_run(job.name)
        last_run_dt: Optional[datetime] = None
        if last_run_record is not None:
            last_run_dt = last_run_record.started_at

        expected = checker.expected_last_run(now)
        overdue = checker.is_overdue(now)

        # Estimate next expected run as one interval after expected_last_run.
        next_expected: Optional[datetime] = None
        seconds_until: Optional[float] = None
        if expected is not None:
            try:
                from croniter import croniter  # type: ignore
                ci = croniter(job.schedule, now)
                next_expected = ci.get_next(datetime).replace(tzinfo=timezone.utc)
                seconds_until = (next_expected - now).total_seconds()
            except Exception:
                pass

        return RunPlan(
            job_name=job.name,
            last_run=last_run_dt,
            next_expected=next_expected,
            is_overdue=overdue,
            seconds_until_due=seconds_until,
        )

    def plan_all(self, jobs: list[JobConfig], now: Optional[datetime] = None) -> list[RunPlan]:
        """Return plans for every job in *jobs*."""
        return [self.plan(j, now) for j in jobs]
