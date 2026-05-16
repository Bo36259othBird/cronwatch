"""Tracks whether a job is within a post-run cooldown window."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwatch.store import JobStore


@dataclass
class CooldownStatus:
    job_name: str
    last_finished: Optional[datetime]
    cooldown_seconds: int
    in_cooldown: bool
    remaining_seconds: float

    def is_ready(self) -> bool:
        """Return True when the job is allowed to run again."""
        return not self.in_cooldown


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class RunCooldownChecker:
    """Check whether a job has waited long enough since its last completed run."""

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def check(self, job_name: str, cooldown_seconds: int) -> CooldownStatus:
        """Return a CooldownStatus for *job_name* given *cooldown_seconds*."""
        run = self._store.get_last_run(job_name)

        if run is None or run.finished_at is None:
            return CooldownStatus(
                job_name=job_name,
                last_finished=None,
                cooldown_seconds=cooldown_seconds,
                in_cooldown=False,
                remaining_seconds=0.0,
            )

        elapsed = (_utcnow() - run.finished_at).total_seconds()
        remaining = max(0.0, cooldown_seconds - elapsed)
        in_cooldown = remaining > 0

        return CooldownStatus(
            job_name=job_name,
            last_finished=run.finished_at,
            cooldown_seconds=cooldown_seconds,
            in_cooldown=in_cooldown,
            remaining_seconds=remaining,
        )

    def check_all(
        self, job_cooldowns: dict[str, int]
    ) -> list[CooldownStatus]:
        """Return a CooldownStatus for every entry in *job_cooldowns*."""
        return [
            self.check(name, secs)
            for name, secs in sorted(job_cooldowns.items())
        ]
