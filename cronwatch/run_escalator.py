"""Escalation logic: upgrade alert severity after repeated failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cronwatch.store import JobStore


@dataclass
class EscalationLevel:
    job_name: str
    level: int          # 0 = normal, 1 = warning, 2 = critical
    consecutive_failures: int
    first_failure_at: Optional[datetime]
    last_failure_at: Optional[datetime]

    @property
    def label(self) -> str:
        return ["normal", "warning", "critical"][min(self.level, 2)]

    @property
    def is_elevated(self) -> bool:
        return self.level > 0


@dataclass
class EscalationPolicy:
    warning_threshold: int = 2   # failures before warning
    critical_threshold: int = 5  # failures before critical


class RunEscalator:
    """Track consecutive failure counts and derive escalation levels."""

    def __init__(self, store: JobStore, policy: Optional[EscalationPolicy] = None) -> None:
        self._store = store
        self._policy = policy or EscalationPolicy()

    def evaluate(self, job_name: str) -> EscalationLevel:
        runs = self._store.get_runs(job_name)
        completed = [r for r in runs if r.finished_at is not None]
        completed.sort(key=lambda r: r.finished_at)  # type: ignore[arg-type]

        consecutive = 0
        first_at: Optional[datetime] = None
        last_at: Optional[datetime] = None

        for run in reversed(completed):
            if run.exit_code != 0:
                consecutive += 1
                last_at = last_at or run.finished_at
                first_at = run.finished_at
            else:
                break

        level = 0
        if consecutive >= self._policy.critical_threshold:
            level = 2
        elif consecutive >= self._policy.warning_threshold:
            level = 1

        return EscalationLevel(
            job_name=job_name,
            level=level,
            consecutive_failures=consecutive,
            first_failure_at=first_at,
            last_failure_at=last_at,
        )

    def evaluate_all(self, job_names: List[str]) -> Dict[str, EscalationLevel]:
        return {name: self.evaluate(name) for name in job_names}
