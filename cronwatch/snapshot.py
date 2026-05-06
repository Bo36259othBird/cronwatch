"""Snapshot module: capture and persist a point-in-time summary of all job states."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class JobSnapshot:
    name: str
    last_run_at: Optional[str]  # ISO-8601 or None
    last_exit_code: Optional[int]
    last_duration_seconds: Optional[float]
    is_silent: bool


@dataclass
class Snapshot:
    captured_at: str  # ISO-8601
    jobs: List[JobSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        jobs = [JobSnapshot(**j) for j in data.get("jobs", [])]
        return cls(captured_at=data["captured_at"], jobs=jobs)


class SnapshotWriter:
    """Writes Snapshot objects to a JSON file."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def write(self, snapshot: Snapshot) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(snapshot.to_dict(), fh, indent=2)

    def read(self) -> Optional[Snapshot]:
        if not self._path.exists():
            return None
        with self._path.open("r", encoding="utf-8") as fh:
            return Snapshot.from_dict(json.load(fh))


def build_snapshot(
    job_names: List[str],
    store,  # JobStore
    silence_detector,  # SilenceDetector
) -> Snapshot:
    """Create a Snapshot by querying the store and silence detector."""
    now = datetime.now(timezone.utc).isoformat()
    jobs: List[JobSnapshot] = []
    for name in job_names:
        run = store.get_last_run(name)
        jobs.append(
            JobSnapshot(
                name=name,
                last_run_at=run.started_at.isoformat() if run and run.started_at else None,
                last_exit_code=run.exit_code if run else None,
                last_duration_seconds=(
                    (run.finished_at - run.started_at).total_seconds()
                    if run and run.finished_at and run.started_at
                    else None
                ),
                is_silent=name in silence_detector.silent_jobs(),
            )
        )
    return Snapshot(captured_at=now, jobs=jobs)
