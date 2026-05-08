"""Profile job runs by computing timing percentiles and flagging outliers."""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import List, Optional

from cronwatch.store import JobStore


@dataclass
class RunProfile:
    job_name: str
    run_count: int
    p50: Optional[float]  # median duration in seconds
    p95: Optional[float]
    p99: Optional[float]
    mean: Optional[float]
    stddev: Optional[float]

    def is_outlier(self, duration_seconds: float, threshold: float = 2.0) -> bool:
        """Return True if duration is more than *threshold* stddevs from mean."""
        if self.mean is None or self.stddev is None or self.stddev == 0:
            return False
        return abs(duration_seconds - self.mean) > threshold * self.stddev


def _percentile(data: List[float], pct: float) -> float:
    """Compute percentile using nearest-rank method."""
    data = sorted(data)
    idx = max(0, int(len(data) * pct / 100) - 1)
    return data[idx]


class RunProfiler:
    def __init__(self, store: JobStore) -> None:
        self._store = store

    def profile(self, job_name: str, limit: int = 200) -> RunProfile:
        """Build a RunProfile from the most recent *limit* completed runs."""
        runs = self._store.get_runs(job_name, limit=limit)
        durations = [
            (r.finished_at - r.started_at).total_seconds()
            for r in runs
            if r.finished_at is not None
        ]
        if not durations:
            return RunProfile(
                job_name=job_name,
                run_count=0,
                p50=None, p95=None, p99=None,
                mean=None, stddev=None,
            )
        return RunProfile(
            job_name=job_name,
            run_count=len(durations),
            p50=_percentile(durations, 50),
            p95=_percentile(durations, 95),
            p99=_percentile(durations, 99),
            mean=statistics.mean(durations),
            stddev=statistics.pstdev(durations) if len(durations) > 1 else 0.0,
        )
