"""Verify run integrity by checking for anomalous exit codes and duration bounds."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from cronwatch.store import JobStore, JobRun


@dataclass
class VerificationResult:
    job_name: str
    run_id: int
    passed: bool
    reasons: List[str]

    @property
    def failed(self) -> bool:
        return not self.passed


def _duration(run: JobRun) -> Optional[float]:
    if run.started_at is None or run.finished_at is None:
        return None
    return (run.finished_at - run.started_at).total_seconds()


class RunVerifier:
    """Verify that a completed run meets basic integrity constraints."""

    def __init__(
        self,
        store: JobStore,
        max_duration_seconds: Optional[float] = None,
        allowed_exit_codes: Optional[List[int]] = None,
    ) -> None:
        self._store = store
        self._max_duration = max_duration_seconds
        self._allowed_codes = set(allowed_exit_codes) if allowed_exit_codes is not None else {0}

    def verify(self, job_name: str, run_id: int) -> VerificationResult:
        """Verify a single run by run_id. Returns a VerificationResult."""
        run = self._store.get_run(run_id)
        reasons: List[str] = []

        if run is None:
            return VerificationResult(
                job_name=job_name,
                run_id=run_id,
                passed=False,
                reasons=[f"run {run_id} not found in store"],
            )

        if run.exit_code is None:
            reasons.append("exit code is missing (run may still be active)")
        elif run.exit_code not in self._allowed_codes:
            reasons.append(
                f"exit code {run.exit_code} not in allowed set {sorted(self._allowed_codes)}"
            )

        dur = _duration(run)
        if dur is None:
            reasons.append("duration could not be computed (missing timestamps)")
        elif self._max_duration is not None and dur > self._max_duration:
            reasons.append(
                f"duration {dur:.1f}s exceeds maximum {self._max_duration:.1f}s"
            )

        return VerificationResult(
            job_name=job_name,
            run_id=run_id,
            passed=len(reasons) == 0,
            reasons=reasons,
        )

    def verify_all(self, job_name: str) -> List[VerificationResult]:
        """Verify every recorded run for *job_name*."""
        runs = self._store.get_runs(job_name)
        return [self.verify(job_name, r.id) for r in runs]
