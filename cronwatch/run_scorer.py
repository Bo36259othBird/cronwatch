"""Assigns a health score (0-100) to a job based on recent run history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobStore


_WEIGHT_SUCCESS_RATE = 0.50
_WEIGHT_STABILITY = 0.25
_WEIGHT_RECENCY = 0.25


@dataclass
class JobScore:
    job_name: str
    score: int  # 0-100
    success_rate: float
    is_stable: bool
    has_recent_run: bool
    grade: str

    @staticmethod
    def grade_from_score(score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 40:
            return "D"
        return "F"


class RunScorer:
    """Compute a composite health score for a job."""

    def __init__(self, store: JobStore, window: int = 20) -> None:
        self._store = store
        self._window = window

    def score(self, job_name: str) -> Optional[JobScore]:
        runs = self._store.get_runs(job_name, limit=self._window)
        if not runs:
            return None

        completed = [r for r in runs if r.exit_code is not None]
        if not completed:
            return None

        successes = sum(1 for r in completed if r.exit_code == 0)
        success_rate = successes / len(completed)

        durations = [
            (r.finished_at - r.started_at).total_seconds()
            for r in completed
            if r.finished_at is not None
        ]
        is_stable = False
        if len(durations) >= 2:
            avg = sum(durations) / len(durations)
            variance = sum((d - avg) ** 2 for d in durations) / len(durations)
            cv = (variance ** 0.5 / avg) if avg > 0 else 0.0
            is_stable = cv < 0.5

        latest = max(completed, key=lambda r: r.started_at)
        from datetime import datetime, timezone
        age_hours = (
            datetime.now(timezone.utc) - latest.started_at
        ).total_seconds() / 3600
        has_recent_run = age_hours <= 25

        raw = (
            success_rate * _WEIGHT_SUCCESS_RATE
            + (1.0 if is_stable else 0.0) * _WEIGHT_STABILITY
            + (1.0 if has_recent_run else 0.0) * _WEIGHT_RECENCY
        )
        score_int = round(raw * 100)

        return JobScore(
            job_name=job_name,
            score=score_int,
            success_rate=success_rate,
            is_stable=is_stable,
            has_recent_run=has_recent_run,
            grade=JobScore.grade_from_score(score_int),
        )
