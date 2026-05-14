"""Detect anomalous job runs based on duration deviation from historical mean."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class AnomalyResult:
    job_name: str
    run_id: int
    duration: float
    mean_duration: float
    std_duration: float
    z_score: float
    is_anomaly: bool

    @property
    def deviation_pct(self) -> float:
        """Percentage deviation from mean."""
        if self.mean_duration == 0:
            return 0.0
        return ((self.duration - self.mean_duration) / self.mean_duration) * 100.0


class RunAnomalyDetector:
    """Detect anomalous run durations using z-score analysis."""

    def __init__(self, store: JobStore, threshold: float = 2.5, min_samples: int = 5) -> None:
        self._store = store
        self._threshold = threshold
        self._min_samples = min_samples

    def _completed_durations(self, job_name: str) -> List[float]:
        runs = self._store.get_runs(job_name)
        return [
            (r.finished_at - r.started_at).total_seconds()
            for r in runs
            if r.finished_at is not None
        ]

    def analyze(self, job_name: str, run_id: int) -> Optional[AnomalyResult]:
        """Analyze a single run for anomaly. Returns None if insufficient data."""
        run: Optional[JobRun] = self._store.get_run(run_id)
        if run is None or run.finished_at is None:
            return None

        durations = self._completed_durations(job_name)
        if len(durations) < self._min_samples:
            return None

        duration = (run.finished_at - run.started_at).total_seconds()
        mu = mean(durations)
        sigma = stdev(durations)

        if sigma == 0:
            z = 0.0
        else:
            z = (duration - mu) / sigma

        return AnomalyResult(
            job_name=job_name,
            run_id=run_id,
            duration=duration,
            mean_duration=mu,
            std_duration=sigma,
            z_score=z,
            is_anomaly=abs(z) >= self._threshold,
        )

    def anomalies(self, job_name: str) -> List[AnomalyResult]:
        """Return all anomalous completed runs for a job."""
        runs = self._store.get_runs(job_name)
        durations = self._completed_durations(job_name)
        if len(durations) < self._min_samples:
            return []

        mu = mean(durations)
        sigma = stdev(durations)
        results = []
        for run in runs:
            if run.finished_at is None:
                continue
            d = (run.finished_at - run.started_at).total_seconds()
            z = 0.0 if sigma == 0 else (d - mu) / sigma
            if abs(z) >= self._threshold:
                results.append(
                    AnomalyResult(
                        job_name=job_name,
                        run_id=run.run_id,
                        duration=d,
                        mean_duration=mu,
                        std_duration=sigma,
                        z_score=z,
                        is_anomaly=True,
                    )
                )
        return results
