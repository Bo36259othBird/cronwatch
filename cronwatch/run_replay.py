"""Replay analysis: identify runs that are candidates for re-execution based
on failure patterns and recency."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from cronwatch.store import JobRun, JobStore


@dataclass
class ReplayCandidate:
    job_name: str
    run_id: int
    started_at: datetime
    exit_code: Optional[int]
    reason: str

    @property
    def is_failure(self) -> bool:
        return self.exit_code != 0


class RunReplayer:
    """Scan recent runs and surface candidates worth replaying."""

    def __init__(self, store: JobStore, lookback: int = 10) -> None:
        self._store = store
        self._lookback = lookback

    def candidates(self, job_name: str) -> List[ReplayCandidate]:
        """Return runs that failed or produced a non-zero exit code."""
        runs = self._store.get_runs(job_name, limit=self._lookback)
        result: List[ReplayCandidate] = []
        for run in runs:
            if not _is_complete(run):
                continue
            if run.exit_code != 0:
                reason = (
                    f"exit_code={run.exit_code}"
                    if run.exit_code is not None
                    else "no exit code recorded"
                )
                result.append(
                    ReplayCandidate(
                        job_name=job_name,
                        run_id=run.id,
                        started_at=run.started_at,
                        exit_code=run.exit_code,
                        reason=reason,
                    )
                )
        return result

    def latest_failure(self, job_name: str) -> Optional[ReplayCandidate]:
        """Return the most recent failed run, or None."""
        candidates = self.candidates(job_name)
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.started_at)


def _is_complete(run: JobRun) -> bool:
    return run.finished_at is not None
