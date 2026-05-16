"""Score runs to determine retention priority.

Runs with higher scores are more valuable to keep during pruning.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class RetentionScore:
    run_id: int
    job_name: str
    score: float
    reasons: List[str]

    def is_high_priority(self, threshold: float = 0.6) -> bool:
        """Return True if this run should be kept preferentially."""
        return self.score >= threshold


def _score_run(run: JobRun) -> tuple[float, List[str]]:
    """Compute a 0.0–1.0 retention score for a single run."""
    score = 0.0
    reasons: List[str] = []

    # Failures are always worth keeping for debugging
    if run.exit_code not in (None, 0):
        score += 0.5
        reasons.append("failure")

    # Long-running jobs carry more diagnostic value
    if run.started_at and run.finished_at:
        duration = (run.finished_at - run.started_at).total_seconds()
        if duration >= 3600:
            score += 0.3
            reasons.append("long_duration")
        elif duration >= 300:
            score += 0.1
            reasons.append("moderate_duration")

    # Incomplete runs (no finish recorded) are interesting
    if run.finished_at is None:
        score += 0.2
        reasons.append("incomplete")

    return min(score, 1.0), reasons


class RetentionScorer:
    def __init__(self, store: JobStore) -> None:
        self._store = store

    def score_job(self, job_name: str, limit: int = 100) -> List[RetentionScore]:
        """Return scored runs for *job_name*, newest first."""
        runs = self._store.get_runs(job_name, limit=limit)
        results: List[RetentionScore] = []
        for run in runs:
            s, reasons = _score_run(run)
            results.append(
                RetentionScore(
                    run_id=run.id,
                    job_name=job_name,
                    score=s,
                    reasons=reasons,
                )
            )
        return results

    def high_priority_ids(self, job_name: str, threshold: float = 0.6) -> List[int]:
        """Return run IDs that exceed *threshold* and should be preserved."""
        return [
            rs.run_id
            for rs in self.score_job(job_name)
            if rs.is_high_priority(threshold)
        ]
