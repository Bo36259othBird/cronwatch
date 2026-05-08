"""Establish and compare job run baselines (expected duration windows)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class Baseline:
    job_name: str
    mean_duration: Optional[float]   # seconds
    std_duration: Optional[float]    # seconds
    sample_size: int

    @property
    def lower_bound(self) -> Optional[float]:
        if self.mean_duration is None or self.std_duration is None:
            return None
        return max(0.0, self.mean_duration - 2 * self.std_duration)

    @property
    def upper_bound(self) -> Optional[float]:
        if self.mean_duration is None or self.std_duration is None:
            return None
        return self.mean_duration + 2 * self.std_duration

    def within_bounds(self, duration: float) -> bool:
        """Return True when *duration* falls inside the 2-sigma window."""
        lo, hi = self.lower_bound, self.upper_bound
        if lo is None or hi is None:
            return True
        return lo <= duration <= hi


class RunBaselineCollector:
    """Compute duration baselines from stored job runs."""

    _MIN_SAMPLES = 3

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def collect(self, job_name: str, limit: int = 50) -> Baseline:
        runs = [
            r for r in self._store.get_runs(job_name, limit=limit)
            if r.duration is not None
        ]
        if len(runs) < self._MIN_SAMPLES:
            return Baseline(
                job_name=job_name,
                mean_duration=None,
                std_duration=None,
                sample_size=len(runs),
            )
        durations = [r.duration for r in runs]  # type: ignore[misc]
        mean = sum(durations) / len(durations)
        variance = sum((d - mean) ** 2 for d in durations) / len(durations)
        std = variance ** 0.5
        return Baseline(
            job_name=job_name,
            mean_duration=mean,
            std_duration=std,
            sample_size=len(durations),
        )
