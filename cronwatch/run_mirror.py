"""Mirror runs across two job names to detect divergence in outcomes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobStore, JobRun


@dataclass
class MirrorResult:
    job_a: str
    job_b: str
    runs_a: int
    runs_b: int
    failures_a: int
    failures_b: int
    diverged: bool
    divergence_pct: Optional[float]

    @property
    def success_rate_a(self) -> Optional[float]:
        if self.runs_a == 0:
            return None
        return (self.runs_a - self.failures_a) / self.runs_a

    @property
    def success_rate_b(self) -> Optional[float]:
        if self.runs_b == 0:
            return None
        return (self.runs_b - self.failures_b) / self.runs_b


def _count_failures(runs: list[JobRun]) -> int:
    return sum(1 for r in runs if r.exit_code not in (None, 0))


class RunMirror:
    """Compare execution outcomes between two mirrored jobs."""

    def __init__(self, store: JobStore, divergence_threshold: float = 0.10) -> None:
        self._store = store
        self._threshold = divergence_threshold

    def compare(self, job_a: str, job_b: str, limit: int = 50) -> MirrorResult:
        runs_a = self._store.get_runs(job_a, limit=limit)
        runs_b = self._store.get_runs(job_b, limit=limit)

        failures_a = _count_failures(runs_a)
        failures_b = _count_failures(runs_b)

        rate_a = (failures_a / len(runs_a)) if runs_a else None
        rate_b = (failures_b / len(runs_b)) if runs_b else None

        if rate_a is None or rate_b is None:
            diverged = False
            divergence_pct = None
        else:
            divergence_pct = abs(rate_a - rate_b)
            diverged = divergence_pct >= self._threshold

        return MirrorResult(
            job_a=job_a,
            job_b=job_b,
            runs_a=len(runs_a),
            runs_b=len(runs_b),
            failures_a=failures_a,
            failures_b=failures_b,
            diverged=diverged,
            divergence_pct=round(divergence_pct * 100, 2) if divergence_pct is not None else None,
        )
