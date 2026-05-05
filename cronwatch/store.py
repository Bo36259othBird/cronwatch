"""Persistent storage for job run records (SQLite-backed)."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class JobRun:
    run_id: int
    job_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None


def is_complete(run: JobRun) -> bool:
    return run.finished_at is not None and run.exit_code is not None


class JobStore:
    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_runs (
                run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name    TEXT NOT NULL,
                started_at  TEXT NOT NULL,
                finished_at TEXT,
                exit_code   INTEGER
            )
            """
        )
        self._conn.commit()

    def record_start(self, job_name: str) -> int:
        cur = self._conn.execute(
            "INSERT INTO job_runs (job_name, started_at) VALUES (?, ?)",
            (job_name, datetime.utcnow().isoformat()),
        )
        self._conn.commit()
        return cur.lastrowid

    def record_finish(self, run_id: int, exit_code: int) -> None:
        self._conn.execute(
            "UPDATE job_runs SET finished_at = ?, exit_code = ? WHERE run_id = ?",
            (datetime.utcnow().isoformat(), exit_code, run_id),
        )
        self._conn.commit()

    def get_last_run(self, job_name: str) -> Optional[JobRun]:
        cur = self._conn.execute(
            "SELECT run_id, job_name, started_at, finished_at, exit_code "
            "FROM job_runs WHERE job_name = ? ORDER BY run_id DESC LIMIT 1",
            (job_name,),
        )
        row = cur.fetchone()
        return self._row_to_run(row) if row else None

    def get_runs_since(self, job_name: str, since: datetime) -> List[JobRun]:
        cur = self._conn.execute(
            "SELECT run_id, job_name, started_at, finished_at, exit_code "
            "FROM job_runs WHERE job_name = ? AND started_at >= ? ORDER BY run_id ASC",
            (job_name, since.isoformat()),
        )
        return [self._row_to_run(row) for row in cur.fetchall()]

    def all_runs(self, job_name: str) -> List[JobRun]:
        cur = self._conn.execute(
            "SELECT run_id, job_name, started_at, finished_at, exit_code "
            "FROM job_runs WHERE job_name = ? ORDER BY run_id ASC",
            (job_name,),
        )
        return [self._row_to_run(row) for row in cur.fetchall()]

    @staticmethod
    def _row_to_run(row) -> JobRun:
        run_id, job_name, started_at, finished_at, exit_code = row
        return JobRun(
            run_id=run_id,
            job_name=job_name,
            started_at=datetime.fromisoformat(started_at),
            finished_at=datetime.fromisoformat(finished_at) if finished_at else None,
            exit_code=exit_code,
        )
