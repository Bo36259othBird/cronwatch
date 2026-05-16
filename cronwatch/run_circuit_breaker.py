"""Circuit breaker that trips when a job's failure rate exceeds a threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class CircuitState:
    job_name: str
    is_open: bool          # True = tripped / circuit open
    failure_count: int
    total_count: int
    tripped_at: Optional[datetime]
    threshold: float       # 0.0 – 1.0

    @property
    def failure_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.failure_count / self.total_count

    def is_tripped(self) -> bool:
        return self.is_open


class RunCircuitBreaker:
    """Evaluate whether a job's circuit should be considered open (tripped).

    A circuit trips when the failure_rate over the last *window* runs
    exceeds *threshold*.  It resets automatically once the rate drops back
    below the threshold.
    """

    def __init__(
        self,
        store: JobStore,
        threshold: float = 0.5,
        window: int = 10,
    ) -> None:
        if not (0.0 < threshold <= 1.0):
            raise ValueError("threshold must be in (0, 1]")
        if window < 1:
            raise ValueError("window must be >= 1")
        self._store = store
        self._threshold = threshold
        self._window = window
        self._tripped_at: dict[str, datetime] = {}

    def evaluate(self, job_name: str) -> CircuitState:
        """Return the current CircuitState for *job_name*."""
        runs = self._store.get_runs(job_name, limit=self._window)
        completed = [r for r in runs if r.exit_code is not None]
        total = len(completed)
        failures = sum(1 for r in completed if r.exit_code != 0)

        rate = failures / total if total else 0.0
        is_open = total > 0 and rate >= self._threshold

        if is_open and job_name not in self._tripped_at:
            self._tripped_at[job_name] = datetime.now(tz=timezone.utc)
        elif not is_open and job_name in self._tripped_at:
            del self._tripped_at[job_name]

        return CircuitState(
            job_name=job_name,
            is_open=is_open,
            failure_count=failures,
            total_count=total,
            tripped_at=self._tripped_at.get(job_name),
            threshold=self._threshold,
        )

    def open_circuits(self, job_names: list[str]) -> list[CircuitState]:
        """Return only the tripped circuits from *job_names*."""
        return [s for name in job_names if (s := self.evaluate(name)).is_open]
