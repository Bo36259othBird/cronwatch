"""Export job run records to CSV or JSON for external analysis."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import List, Optional

from cronwatch.store import JobRun, JobStore


def _run_to_dict(run: JobRun) -> dict:
    d = asdict(run)
    # Ensure datetime fields are serialised as ISO strings
    for key in ("started_at", "finished_at"):
        val = d.get(key)
        if val is not None and hasattr(val, "isoformat"):
            d[key] = val.isoformat()
    return d


class RunExporter:
    """Exports job runs from the store to CSV or JSON."""

    _FIELDS = ["id", "job_name", "started_at", "finished_at", "exit_code", "error"]

    def __init__(self, store: JobStore) -> None:
        self._store = store

    def export_json(
        self, job_name: str, limit: Optional[int] = None
    ) -> str:
        """Return a JSON string of run records for *job_name*."""
        runs = self._fetch(job_name, limit)
        return json.dumps([_run_to_dict(r) for r in runs], indent=2)

    def export_csv(
        self, job_name: str, limit: Optional[int] = None
    ) -> str:
        """Return a CSV string of run records for *job_name*."""
        runs = self._fetch(job_name, limit)
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=self._FIELDS, extrasaction="ignore")
        writer.writeheader()
        for run in runs:
            writer.writerow(_run_to_dict(run))
        return buf.getvalue()

    def _fetch(self, job_name: str, limit: Optional[int]) -> List[JobRun]:
        runs = self._store.get_runs(job_name)
        if limit is not None:
            runs = runs[:limit]
        return runs
