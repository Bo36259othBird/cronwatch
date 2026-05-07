"""Attach and retrieve free-form labels (key/value pairs) on job runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.store import JobStore


@dataclass
class RunLabel:
    run_id: int
    job_name: str
    key: str
    value: str


class RunLabeler:
    """Persist and query labels attached to individual job runs."""

    def __init__(self, store: JobStore) -> None:
        self._store = store
        self._init_table()

    # ------------------------------------------------------------------
    # schema
    # ------------------------------------------------------------------

    def _init_table(self) -> None:
        with self._store._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_labels (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id   INTEGER NOT NULL,
                    job_name TEXT    NOT NULL,
                    key      TEXT    NOT NULL,
                    value    TEXT    NOT NULL
                )
                """
            )

    # ------------------------------------------------------------------
    # write
    # ------------------------------------------------------------------

    def set_label(self, run_id: int, job_name: str, key: str, value: str) -> None:
        """Insert or replace a label for the given run."""
        with self._store._conn() as conn:
            conn.execute(
                """
                INSERT INTO run_labels (run_id, job_name, key, value)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, job_name, key, value),
            )

    def remove_label(self, run_id: int, key: str) -> None:
        """Remove a specific label from a run."""
        with self._store._conn() as conn:
            conn.execute(
                "DELETE FROM run_labels WHERE run_id = ? AND key = ?",
                (run_id, key),
            )

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------

    def get_labels(self, run_id: int) -> Dict[str, str]:
        """Return all labels for a run as a plain dict."""
        with self._store._conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM run_labels WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        return {row[0]: row[1] for row in rows}

    def runs_with_label(self, job_name: str, key: str, value: Optional[str] = None) -> List[int]:
        """Return run IDs for *job_name* that carry *key* (optionally matching *value*)."""
        with self._store._conn() as conn:
            if value is None:
                rows = conn.execute(
                    "SELECT run_id FROM run_labels WHERE job_name = ? AND key = ?",
                    (job_name, key),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT run_id FROM run_labels WHERE job_name = ? AND key = ? AND value = ?",
                    (job_name, key, value),
                ).fetchall()
        return [row[0] for row in rows]
