"""Persistent storage for cron job execution records."""

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional


@dataclass
class JobRun:
    job_name: str
    started_at: float
    finished_at: Optional[float] = None
    exit_code: Optional[int] = None
    duration: Optional[float] = None
    success: Optional[bool] = None

    @property
    def is_complete(self) -> bool:
        return self.finished_at is not None


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS job_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name    TEXT    NOT NULL,
    started_at  REAL    NOT NULL,
    finished_at REAL,
    exit_code   INTEGER,
    duration    REAL,
    success     INTEGER
);
"""


class JobStore:
    def __init__(self, db_path: str = "cronwatch.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(CREATE_TABLE_SQL)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def record_start(self, job_name: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO job_runs (job_name, started_at) VALUES (?, ?)",
                (job_name, time.time()),
            )
            return cur.lastrowid

    def record_finish(self, run_id: int, exit_code: int) -> None:
        finished_at = time.time()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT started_at FROM job_runs WHERE id = ?", (run_id,)
            ).fetchone()
            duration = finished_at - row["started_at"] if row else None
            success = exit_code == 0
            conn.execute(
                """UPDATE job_runs
                   SET finished_at=?, exit_code=?, duration=?, success=?
                   WHERE id=?""",
                (finished_at, exit_code, duration, int(success), run_id),
            )

    def get_last_run(self, job_name: str) -> Optional[JobRun]:
        with self._conn() as conn:
            row = conn.execute(
                """SELECT * FROM job_runs WHERE job_name=?
                   ORDER BY started_at DESC LIMIT 1""",
                (job_name,),
            ).fetchone()
        if row is None:
            return None
        return JobRun(**{k: row[k] for k in row.keys() if k != "id"})

    def get_runs(self, job_name: str, limit: int = 50) -> List[JobRun]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM job_runs WHERE job_name=?
                   ORDER BY started_at DESC LIMIT ?""",
                (job_name, limit),
            ).fetchall()
        return [JobRun(**{k: row[k] for k in row.keys() if k != "id"}) for row in rows]
