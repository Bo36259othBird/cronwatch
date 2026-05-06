"""Scheduler: parses cron expressions and determines if a job is overdue."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from croniter import croniter

from cronwatch.config import JobConfig


class ScheduleChecker:
    """Determines whether a cron job is overdue based on its schedule."""

    def __init__(self, now_fn=None):
        """
        Args:
            now_fn: Callable returning current UTC datetime. Defaults to
                    ``datetime.now(timezone.utc)``. Useful for testing.
        """
        self._now = now_fn or (lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def expected_last_run(self, schedule: str, reference: Optional[datetime] = None) -> datetime:
        """Return the most recent expected run time before *reference*.

        Args:
            schedule: A standard 5-field cron expression (e.g. ``"*/5 * * * *"``).
            reference: The point in time to look back from. Defaults to now.

        Returns:
            A timezone-aware UTC datetime of the last scheduled tick.
        """
        ref = reference or self._now()
        # croniter works in local time; we pass a UTC-naive datetime and
        # treat the result as UTC throughout.
        ref_naive = ref.replace(tzinfo=None)
        itr = croniter(schedule, ref_naive)
        prev_naive: datetime = itr.get_prev(datetime)  # type: ignore[assignment]
        return prev_naive.replace(tzinfo=timezone.utc)

    def is_overdue(self, job: JobConfig, last_run: Optional[datetime]) -> bool:
        """Return True when *job* has not run since its last expected tick.

        A job is considered overdue when:
        - It has never run (``last_run`` is ``None``), **and** the expected
          last tick is older than ``silence_threshold`` seconds, OR
        - It has run but not since the expected last tick.

        Args:
            job: The job configuration, including ``schedule`` and
                 ``silence_threshold``.
            last_run: UTC datetime of the most recent completed run, or
                      ``None`` if the job has never run.

        Returns:
            ``True`` if the job is considered overdue.
        """
        now = self._now()
        expected = self.expected_last_run(job.schedule, now)

        if last_run is None:
            # Never ran — overdue only if the window has passed.
            age_seconds = (now - expected).total_seconds()
            return age_seconds >= job.silence_threshold

        # Strip tz info for safe comparison if last_run is naive.
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)

        return last_run < expected
