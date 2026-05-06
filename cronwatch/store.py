"""Persistent store for job run records (SQLite)."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, List, Optional


@dataclass
class JobRun:
    id: int
    job_name: str
    started_at: datetime
    finished_at: Optional[datetime]
    success: Optional[bool]
    exit_code: Optional[int]


def is_complete(run: JobRun) -> bool:
    return run.finished_at is not None


class JobStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_runs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name    TEXT    NOT NULL,
                    started_at  REAL    NOT NULL,
                    finished_at REAL,
                    success     INTEGER,
                    exit_code   INTEGER
                )
                """
            )

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def record_start(self, job_name: str, started_at: Optional[datetime] = None) -> int:
        if started_at is None:
            started_at = datetime.utcnow()
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO job_runs (job_name, started_at) VALUES (?, ?)",
                (job_name, started_at.timestamp()),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def record_finish(
        self,
        run_id: int,
        success: bool,
        exit_code: int,
        finished_at: Optional[datetime] = None,
    ) -> None:
        if finished_at is None:
            finished_at = datetime.utcnow()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE job_runs
                SET finished_at = ?, success = ?, exit_code = ?
                WHERE id = ?
                """,
                (finished_at.timestamp(), int(success), exit_code, run_id),
            )

    def get_last_run(self, job_name: str) -> Optional[JobRun]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM job_runs WHERE job_name = ? ORDER BY started_at DESC LIMIT 1",
                (job_name,),
            ).fetchone()
        return self._row_to_run(row) if row else None

    def get_runs(self, job_name: str) -> List[JobRun]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM job_runs WHERE job_name = ? ORDER BY started_at DESC",
                (job_name,),
            ).fetchall()
        return [self._row_to_run(r) for r in rows]

    @staticmethod
    def _row_to_run(row: tuple) -> JobRun:  # type: ignore[type-arg]
        rid, job_name, started_ts, finished_ts, success, exit_code = row
        return JobRun(
            id=rid,
            job_name=job_name,
            started_at=datetime.utcfromtimestamp(started_ts),
            finished_at=datetime.utcfromtimestamp(finished_ts) if finished_ts else None,
            success=bool(success) if success is not None else None,
            exit_code=exit_code,
        )
