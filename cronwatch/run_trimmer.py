"""Trim runs by removing outliers beyond a configurable z-score threshold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import statistics

from cronwatch.store import JobRun, JobStore


@dataclass
class TrimResult:
    job_name: str
    original_count: int
    trimmed_count: int
    removed_ids: List[int]
    mean_duration: Optional[float]
    stdev_duration: Optional[float]

    @property
    def removed_count(self) -> int:
        return len(self.removed_ids)

    @property
    def was_trimmed(self) -> bool:
        return self.removed_count > 0


def _duration(run: JobRun) -> Optional[float]:
    if run.started_at is None or run.finished_at is None:
        return None
    return (run.finished_at - run.started_at).total_seconds()


class RunTrimmer:
    """Remove statistical outlier runs for a job based on duration z-score."""

    def __init__(self, store: JobStore, z_threshold: float = 3.0) -> None:
        self._store = store
        self._z_threshold = z_threshold

    def trim(self, job_name: str) -> TrimResult:
        runs = self._store.get_runs(job_name)
        completed = [r for r in runs if _duration(r) is not None]
        original_count = len(completed)

        if original_count < 3:
            return TrimResult(
                job_name=job_name,
                original_count=original_count,
                trimmed_count=original_count,
                removed_ids=[],
                mean_duration=None,
                stdev_duration=None,
            )

        durations = [_duration(r) for r in completed]  # type: ignore[misc]
        mean = statistics.mean(durations)
        stdev = statistics.pstdev(durations)

        removed_ids: List[int] = []
        if stdev > 0:
            for run, dur in zip(completed, durations):
                z = abs(dur - mean) / stdev
                if z > self._z_threshold:
                    removed_ids.append(run.id)

        return TrimResult(
            job_name=job_name,
            original_count=original_count,
            trimmed_count=original_count - len(removed_ids),
            removed_ids=removed_ids,
            mean_duration=round(mean, 4),
            stdev_duration=round(stdev, 4),
        )
