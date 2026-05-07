"""Group job runs by time bucket (hour, day, week) for aggregated analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List

from cronwatch.store import JobRun, JobStore


class Bucket(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"


def _bucket_key(dt: datetime, bucket: Bucket) -> str:
    """Return a string key for the given datetime and bucket size."""
    if bucket == Bucket.HOUR:
        return dt.strftime("%Y-%m-%dT%H")
    if bucket == Bucket.DAY:
        return dt.strftime("%Y-%m-%d")
    # ISO week
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


@dataclass
class RunGroup:
    key: str
    bucket: Bucket
    runs: List[JobRun] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.runs)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.runs if r.exit_code not in (None, 0))

    @property
    def success_rate(self) -> float:
        if not self.runs:
            return 0.0
        completed = [r for r in self.runs if r.exit_code is not None]
        if not completed:
            return 0.0
        successes = sum(1 for r in completed if r.exit_code == 0)
        return successes / len(completed)


class RunGrouper:
    """Groups runs for a specific job by a time bucket."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def group(self, job_name: str, bucket: Bucket) -> Dict[str, RunGroup]:
        """Return an ordered dict of bucket-key -> RunGroup for *job_name*."""
        runs = self._store.get_runs(job_name)
        groups: Dict[str, RunGroup] = {}
        for run in runs:
            ts = run.started_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            key = _bucket_key(ts, bucket)
            if key not in groups:
                groups[key] = RunGroup(key=key, bucket=bucket)
            groups[key].runs.append(run)
        return dict(sorted(groups.items()))
