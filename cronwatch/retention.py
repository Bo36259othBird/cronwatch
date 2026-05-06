"""Retention policy: prune old job run records from the store."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class RetentionPolicy:
    """Describes how long to keep job run history."""

    max_age_days: int = 30
    max_runs_per_job: Optional[int] = None


class RetentionManager:
    """Applies a RetentionPolicy to a JobStore, removing stale records."""

    def __init__(self, store: JobStore, policy: RetentionPolicy) -> None:
        self._store = store
        self._policy = policy

    def prune(self) -> int:
        """Remove records that violate the policy.  Returns number of rows deleted."""
        deleted = 0
        deleted += self._prune_by_age()
        if self._policy.max_runs_per_job is not None:
            deleted += self._prune_by_count()
        return deleted

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _prune_by_age(self) -> int:
        cutoff = datetime.utcnow() - timedelta(days=self._policy.max_age_days)
        cutoff_ts = cutoff.timestamp()
        with self._store._conn() as conn:  # noqa: SLF001
            cur = conn.execute(
                "DELETE FROM job_runs WHERE started_at < ?",
                (cutoff_ts,),
            )
            return cur.rowcount

    def _prune_by_count(self) -> int:
        limit = self._policy.max_runs_per_job
        with self._store._conn() as conn:  # noqa: SLF001
            jobs = [
                row[0]
                for row in conn.execute("SELECT DISTINCT job_name FROM job_runs")
            ]
        total = 0
        for job in jobs:
            total += self._prune_job_count(job, limit)
        return total

    def _prune_job_count(self, job_name: str, limit: int) -> int:
        with self._store._conn() as conn:  # noqa: SLF001
            cur = conn.execute(
                """
                DELETE FROM job_runs
                WHERE job_name = ?
                  AND id NOT IN (
                      SELECT id FROM job_runs
                      WHERE job_name = ?
                      ORDER BY started_at DESC
                      LIMIT ?
                  )
                """,
                (job_name, job_name, limit),
            )
            return cur.rowcount
