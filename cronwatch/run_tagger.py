"""Attach and retrieve free-form tags on individual job runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from cronwatch.store import JobStore


@dataclass
class RunTagSet:
    """Collection of tags attached to a single run."""

    run_id: int
    job_name: str
    tags: List[str] = field(default_factory=list)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


class RunTagger:
    """Persist and query tags on job runs using the existing SQLite store."""

    def __init__(self, store: JobStore) -> None:
        self._store = store
        self._init_table()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_table(self) -> None:
        self._store._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_tags (
                run_id  INTEGER NOT NULL,
                tag     TEXT    NOT NULL,
                PRIMARY KEY (run_id, tag)
            )
            """
        )
        self._store._conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_tag(self, run_id: int, tag: str) -> None:
        """Attach *tag* to *run_id*.  Silently ignores duplicates."""
        tag = tag.strip()
        if not tag:
            raise ValueError("tag must not be empty")
        self._store._conn.execute(
            "INSERT OR IGNORE INTO run_tags (run_id, tag) VALUES (?, ?)",
            (run_id, tag),
        )
        self._store._conn.commit()

    def remove_tag(self, run_id: int, tag: str) -> None:
        """Remove *tag* from *run_id* if it exists."""
        self._store._conn.execute(
            "DELETE FROM run_tags WHERE run_id = ? AND tag = ?",
            (run_id, tag),
        )
        self._store._conn.commit()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_tags(self, run_id: int) -> RunTagSet:
        """Return all tags for *run_id*."""
        run = self._store.get_last_run.__func__  # just need job_name lookup
        # Retrieve job_name from the runs table
        row = self._store._conn.execute(
            "SELECT job_name FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        job_name = row["job_name"] if row else "unknown"
        rows = self._store._conn.execute(
            "SELECT tag FROM run_tags WHERE run_id = ? ORDER BY tag",
            (run_id,),
        ).fetchall()
        return RunTagSet(run_id=run_id, job_name=job_name, tags=[r["tag"] for r in rows])

    def runs_with_tag(self, tag: str) -> List[int]:
        """Return all run IDs that carry *tag*."""
        rows = self._store._conn.execute(
            "SELECT run_id FROM run_tags WHERE tag = ? ORDER BY run_id",
            (tag,),
        ).fetchall()
        return [r["run_id"] for r in rows]

    def all_tags(self) -> Dict[int, List[str]]:
        """Return a mapping of run_id -> sorted list of tags for all tagged runs."""
        rows = self._store._conn.execute(
            "SELECT run_id, tag FROM run_tags ORDER BY run_id, tag"
        ).fetchall()
        result: Dict[int, List[str]] = {}
        for row in rows:
            result.setdefault(row["run_id"], []).append(row["tag"])
        return result
