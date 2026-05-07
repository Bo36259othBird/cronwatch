"""Tracks consecutive success/failure streaks for cron jobs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class Streak:
    job_name: str
    kind: str          # 'success' or 'failure'
    length: int
    is_active: bool    # True if the streak is the most recent run sequence

    @property
    def is_failure_streak(self) -> bool:
        return self.kind == "failure"

    @property
    def is_concerning(self) -> bool:
        """A failure streak of 2+ is worth alerting on."""
        return self.is_failure_streak and self.length >= 2


class RunStreaker:
    """Computes the current and longest streak for a job."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def current_streak(self, job_name: str, limit: int = 50) -> Optional[Streak]:
        """Return the streak at the head of the run history (most recent first)."""
        runs = self._store.get_runs(job_name, limit=limit)
        completed = [r for r in runs if r.exit_code is not None]
        if not completed:
            return None

        first = completed[0]
        kind = "success" if first.exit_code == 0 else "failure"
        length = 0
        for run in completed:
            run_kind = "success" if run.exit_code == 0 else "failure"
            if run_kind == kind:
                length += 1
            else:
                break

        return Streak(job_name=job_name, kind=kind, length=length, is_active=True)

    def longest_failure_streak(self, job_name: str, limit: int = 200) -> int:
        """Return the length of the longest failure streak in the history."""
        runs = self._store.get_runs(job_name, limit=limit)
        completed = [r for r in runs if r.exit_code is not None]
        if not completed:
            return 0

        best = 0
        current = 0
        for run in completed:
            if run.exit_code != 0:
                current += 1
                best = max(best, current)
            else:
                current = 0
        return best
