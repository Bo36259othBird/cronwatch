"""Run budget: track whether jobs complete within a time budget."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from cronwatch.store import JobStore, JobRun


@dataclass
class BudgetResult:
    job_name: str
    run_id: int
    budget_seconds: float
    actual_seconds: Optional[float]
    exceeded: bool
    overage_seconds: Optional[float]

    @property
    def within_budget(self) -> bool:
        return not self.exceeded


def _duration(run: JobRun) -> Optional[float]:
    if run.started_at is None or run.finished_at is None:
        return None
    return (run.finished_at - run.started_at).total_seconds()


class RunBudgetChecker:
    """Check completed runs against per-job time budgets."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def check(self, job_name: str, budget_seconds: float) -> Optional[BudgetResult]:
        """Check the last completed run for *job_name* against *budget_seconds*.

        Returns ``None`` if no completed run exists.
        """
        run = self._store.get_last_run(job_name)
        if run is None:
            return None

        actual = _duration(run)
        if actual is None:
            return None

        exceeded = actual > budget_seconds
        overage = (actual - budget_seconds) if exceeded else None

        return BudgetResult(
            job_name=job_name,
            run_id=run.id,
            budget_seconds=budget_seconds,
            actual_seconds=actual,
            exceeded=exceeded,
            overage_seconds=overage,
        )

    def check_all(
        self, budgets: dict[str, float]
    ) -> List[BudgetResult]:
        """Check every job in *budgets*; skip jobs with no completed run."""
        results: List[BudgetResult] = []
        for job_name, budget in budgets.items():
            result = self.check(job_name, budget)
            if result is not None:
                results.append(result)
        return results
