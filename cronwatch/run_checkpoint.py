"""Track intermediate checkpoints within a running job."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cronwatch.store import JobStore


@dataclass
class Checkpoint:
    run_id: int
    job_name: str
    name: str
    reached_at: datetime
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class CheckpointSummary:
    run_id: int
    job_name: str
    checkpoints: List[Checkpoint]

    @property
    def count(self) -> int:
        return len(self.checkpoints)

    def last(self) -> Optional[Checkpoint]:
        return self.checkpoints[-1] if self.checkpoints else None

    def names(self) -> List[str]:
        return [c.name for c in self.checkpoints]


class RunCheckpointer:
    """Records and retrieves named checkpoints for job runs."""

    def __init__(self, store: JobStore) -> None:
        self._store = store
        self._init_table()

    def _init_table(self) -> None:
        with self._store._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    job_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    reached_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """
            )

    def record(self, run_id: int, job_name: str, name: str,
               metadata: Optional[Dict[str, str]] = None) -> Checkpoint:
        import json
        reached_at = datetime.now(timezone.utc)
        meta = metadata or {}
        with self._store._conn() as conn:
            conn.execute(
                "INSERT INTO run_checkpoints (run_id, job_name, name, reached_at, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (run_id, job_name, name, reached_at.isoformat(), json.dumps(meta)),
            )
        return Checkpoint(run_id=run_id, job_name=job_name, name=name,
                          reached_at=reached_at, metadata=meta)

    def get_summary(self, run_id: int, job_name: str) -> CheckpointSummary:
        import json
        with self._store._conn() as conn:
            rows = conn.execute(
                "SELECT name, reached_at, metadata FROM run_checkpoints "
                "WHERE run_id = ? AND job_name = ? ORDER BY reached_at ASC",
                (run_id, job_name),
            ).fetchall()
        checkpoints = [
            Checkpoint(
                run_id=run_id,
                job_name=job_name,
                name=row[0],
                reached_at=datetime.fromisoformat(row[1]),
                metadata=json.loads(row[2]),
            )
            for row in rows
        ]
        return CheckpointSummary(run_id=run_id, job_name=job_name, checkpoints=checkpoints)
