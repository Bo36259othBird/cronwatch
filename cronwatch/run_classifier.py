"""Classify job runs into categories based on duration and outcome."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobRun, is_complete


CLASS_SUCCESS_FAST = "success_fast"
CLASS_SUCCESS_NORMAL = "success_normal"
CLASS_SUCCESS_SLOW = "success_slow"
CLASS_FAILURE = "failure"
CLASS_INCOMPLETE = "incomplete"


@dataclass
class RunClassification:
    run_id: int
    job_name: str
    category: str
    duration_seconds: Optional[float]

    @property
    def is_success(self) -> bool:
        return self.category in (
            CLASS_SUCCESS_FAST,
            CLASS_SUCCESS_NORMAL,
            CLASS_SUCCESS_SLOW,
        )


class RunClassifier:
    """Classify runs for a given job using configurable duration thresholds."""

    def __init__(
        self,
        fast_threshold: float = 60.0,
        slow_threshold: float = 300.0,
    ) -> None:
        self._fast = fast_threshold
        self._slow = slow_threshold

    def classify(self, run: JobRun) -> RunClassification:
        """Return a RunClassification for *run*."""
        duration: Optional[float] = None

        if not is_complete(run):
            return RunClassification(
                run_id=run.id,
                job_name=run.job_name,
                category=CLASS_INCOMPLETE,
                duration_seconds=None,
            )

        if run.started_at and run.finished_at:
            duration = (run.finished_at - run.started_at).total_seconds()

        if run.exit_code != 0:
            category = CLASS_FAILURE
        elif duration is None:
            category = CLASS_SUCCESS_NORMAL
        elif duration <= self._fast:
            category = CLASS_SUCCESS_FAST
        elif duration >= self._slow:
            category = CLASS_SUCCESS_SLOW
        else:
            category = CLASS_SUCCESS_NORMAL

        return RunClassification(
            run_id=run.id,
            job_name=run.job_name,
            category=category,
            duration_seconds=duration,
        )

    def classify_all(self, runs: list[JobRun]) -> list[RunClassification]:
        """Classify a list of runs."""
        return [self.classify(r) for r in runs]
