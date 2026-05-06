"""Compare two job runs and produce a diff-style summary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.store import JobRun, is_complete


@dataclass
class RunDiff:
    """Difference between two JobRun records."""

    job_name: str
    run_id_a: int
    run_id_b: int
    duration_a: Optional[float]  # seconds, None if incomplete
    duration_b: Optional[float]
    exit_code_a: Optional[int]
    exit_code_b: Optional[int]
    duration_delta: Optional[float]  # b - a, None if either incomplete
    status_changed: bool

    @property
    def slower(self) -> bool:
        """True when run B took longer than run A."""
        if self.duration_delta is None:
            return False
        return self.duration_delta > 0

    @property
    def faster(self) -> bool:
        """True when run B was faster than run A."""
        if self.duration_delta is None:
            return False
        return self.duration_delta < 0


def _duration(run: JobRun) -> Optional[float]:
    if not is_complete(run) or run.started_at is None or run.finished_at is None:
        return None
    return (run.finished_at - run.started_at).total_seconds()


class RunComparator:
    """Compare two runs for the same job."""

    def compare(self, run_a: JobRun, run_b: JobRun) -> RunDiff:
        """Return a :class:`RunDiff` describing how *run_b* differs from *run_a*."""
        if run_a.job_name != run_b.job_name:
            raise ValueError(
                f"Cannot compare runs for different jobs: "
                f"{run_a.job_name!r} vs {run_b.job_name!r}"
            )

        dur_a = _duration(run_a)
        dur_b = _duration(run_b)
        delta = (dur_b - dur_a) if (dur_a is not None and dur_b is not None) else None
        status_changed = run_a.exit_code != run_b.exit_code

        return RunDiff(
            job_name=run_a.job_name,
            run_id_a=run_a.id,
            run_id_b=run_b.id,
            duration_a=dur_a,
            duration_b=dur_b,
            exit_code_a=run_a.exit_code,
            exit_code_b=run_b.exit_code,
            duration_delta=delta,
            status_changed=status_changed,
        )
