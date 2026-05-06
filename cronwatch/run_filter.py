"""Filter and query JobRun records by various criteria."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class RunFilter:
    """Criteria used to narrow down job run results."""

    job_name: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    success_only: bool = False
    failure_only: bool = False
    limit: Optional[int] = None


class RunQuery:
    """Apply a RunFilter against a JobStore and return matching runs."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def query(self, f: RunFilter) -> List[JobRun]:
        """Return runs that satisfy every criterion in *f*."""
        if f.success_only and f.failure_only:
            raise ValueError("success_only and failure_only are mutually exclusive")

        rows: List[JobRun] = self._store.all_runs(f.job_name)

        if f.since is not None:
            rows = [r for r in rows if r.started_at >= f.since]

        if f.until is not None:
            rows = [r for r in rows if r.started_at <= f.until]

        if f.success_only:
            rows = [r for r in rows if r.exit_code == 0]

        if f.failure_only:
            rows = [r for r in rows if r.exit_code is not None and r.exit_code != 0]

        if f.limit is not None:
            rows = rows[: f.limit]

        return rows
