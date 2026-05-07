"""Format run label data for CLI output."""
from __future__ import annotations

import json
from typing import Dict, List


def format_labels(run_id: int, labels: Dict[str, str], fmt: str = "text") -> str:
    """Render *labels* for *run_id* in the requested format."""
    if fmt == "json":
        return _as_json(run_id, labels)
    return _as_text(run_id, labels)


def format_label_runs(job_name: str, key: str, run_ids: List[int], fmt: str = "text") -> str:
    """Render the list of run IDs that carry a given label."""
    if fmt == "json":
        return json.dumps({"job": job_name, "key": key, "run_ids": run_ids}, indent=2)
    lines = [f"Job: {job_name}  label key: {key}"]
    if run_ids:
        lines += [f"  run {rid}" for rid in run_ids]
    else:
        lines.append("  (no matching runs)")
    return "\n".join(lines)


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------


def _as_text(run_id: int, labels: Dict[str, str]) -> str:
    lines = [f"Labels for run {run_id}:"]
    if labels:
        for k, v in sorted(labels.items()):
            lines.append(f"  {k}: {v}")
    else:
        lines.append("  (none)")
    return "\n".join(lines)


def _as_json(run_id: int, labels: Dict[str, str]) -> str:
    return json.dumps({"run_id": run_id, "labels": labels}, indent=2)
