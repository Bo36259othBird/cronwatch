"""Detects and suppresses duplicate job run records within a time window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class DuplicateGroup:
    job_name: str
    run_ids: List[int]
    started_at: datetime
    window_seconds: int

    @property
    def count(self) -> int:
        return len(self.run_ids)

    @property
    def is_duplicate(self) -> bool:
        return self.count > 1


class RunDeduplicator:
    """Identifies runs for the same job that started within a given time window."""

    def __init__(self, store: JobStore, window_seconds: int = 60) -> None:
        self._store = store
        self._window_seconds = window_seconds

    def find_duplicates(self, job_name: str) -> List[DuplicateGroup]:
        """Return groups of runs that appear to be duplicates."""
        runs = self._store.get_runs(job_name)
        if not runs:
            return []

        runs_sorted = sorted(runs, key=lambda r: r.started_at)
        groups: List[DuplicateGroup] = []
        window = timedelta(seconds=self._window_seconds)

        i = 0
        while i < len(runs_sorted):
            anchor = runs_sorted[i]
            cluster: List[int] = [anchor.run_id]
            j = i + 1
            while j < len(runs_sorted):
                candidate = runs_sorted[j]
                if candidate.started_at - anchor.started_at <= window:
                    cluster.append(candidate.run_id)
                    j += 1
                else:
                    break
            if len(cluster) > 1:
                groups.append(
                    DuplicateGroup(
                        job_name=job_name,
                        run_ids=cluster,
                        started_at=anchor.started_at,
                        window_seconds=self._window_seconds,
                    )
                )
            i = j if j > i + 1 else i + 1

        return groups

    def has_duplicates(self, job_name: str) -> bool:
        """Return True if any duplicate groups exist for the given job."""
        return bool(self.find_duplicates(job_name))
