"""Format :class:`~cronwatch.run_annotator.AnnotatedRun` objects for display."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_annotator import AnnotatedRun


def format_annotated_run(run: AnnotatedRun, fmt: str = "text") -> str:
    """Return a human-readable or JSON string for *run*."""
    if fmt == "json":
        return _as_json(run)
    return _as_text(run)


def format_annotated_runs(runs: List[AnnotatedRun], fmt: str = "text") -> str:
    if fmt == "json":
        return json.dumps(
            [
                {
                    "run_id": r.run_id,
                    "job_name": r.job_name,
                    "annotations": r.annotations,
                }
                for r in runs
            ],
            indent=2,
        )
    return "\n".join(_as_text(r) for r in runs)


# ---------------------------------------------------------------------------
# private helpers
# ---------------------------------------------------------------------------


def _as_text(run: AnnotatedRun) -> str:
    lines = [f"Run {run.run_id}  [{run.job_name}]"]
    if run.annotations:
        for k, v in sorted(run.annotations.items()):
            lines.append(f"  {k}: {v}")
    else:
        lines.append("  (no annotations)")
    return "\n".join(lines)


def _as_json(run: AnnotatedRun) -> str:
    return json.dumps(
        {
            "run_id": run.run_id,
            "job_name": run.job_name,
            "annotations": run.annotations,
        },
        indent=2,
    )
