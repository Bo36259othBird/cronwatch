"""Attach freeform annotations (key-value metadata) to completed job runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.store import JobStore


@dataclass
class Annotation:
    run_id: int
    key: str
    value: str


@dataclass
class AnnotatedRun:
    run_id: int
    job_name: str
    annotations: Dict[str, str] = field(default_factory=dict)


class RunAnnotator:
    """Read and write annotations for job runs stored in *store*."""

    def __init__(self, store: JobStore) -> None:
        self._store = store
        self._ensure_table()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def annotate(self, run_id: int, key: str, value: str) -> None:
        """Attach or overwrite *key* on *run_id*."""
        with self._store._conn() as conn:
            conn.execute(
                """
                INSERT INTO run_annotations (run_id, key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(run_id, key) DO UPDATE SET value=excluded.value
                """,
                (run_id, key, value),
            )

    def get(self, run_id: int) -> Dict[str, str]:
        """Return all annotations for *run_id* as a plain dict."""
        with self._store._conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM run_annotations WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        return {row[0]: row[1] for row in rows}

    def delete(self, run_id: int, key: str) -> bool:
        """Remove a single annotation.  Returns True if a row was deleted."""
        with self._store._conn() as conn:
            cur = conn.execute(
                "DELETE FROM run_annotations WHERE run_id = ? AND key = ?",
                (run_id, key),
            )
        return cur.rowcount > 0

    def annotated_run(self, run_id: int, job_name: str) -> AnnotatedRun:
        """Convenience: return an :class:`AnnotatedRun` for *run_id*."""
        return AnnotatedRun(
            run_id=run_id,
            job_name=job_name,
            annotations=self.get(run_id),
        )

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _ensure_table(self) -> None:
        with self._store._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_annotations (
                    run_id  INTEGER NOT NULL,
                    key     TEXT    NOT NULL,
                    value   TEXT    NOT NULL,
                    PRIMARY KEY (run_id, key)
                )
                """
            )
