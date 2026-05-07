"""Format RunGroup collections as text or JSON."""

from __future__ import annotations

import json
from typing import Dict

from cronwatch.run_grouper import Bucket, RunGroup


def format_groups(
    groups: Dict[str, RunGroup],
    job_name: str,
    fmt: str = "text",
) -> str:
    if fmt == "json":
        return _as_json(groups, job_name)
    return _as_text(groups, job_name)


def _as_text(groups: Dict[str, RunGroup], job_name: str) -> str:
    lines = [f"Run groups for job: {job_name}"]
    lines.append("-" * 40)
    if not groups:
        lines.append("  (no runs recorded)")
        return "\n".join(lines)
    for key, grp in groups.items():
        sr = grp.success_rate * 100
        lines.append(
            f"  {key}  runs={grp.count}  failures={grp.failure_count}"
            f"  success_rate={sr:.1f}%"
        )
    return "\n".join(lines)


def _as_json(
    groups: Dict[str, RunGroup], job_name: str
) -> str:
    payload = {
        "job": job_name,
        "groups": [
            {
                "key": key,
                "bucket": grp.bucket.value,
                "count": grp.count,
                "failures": grp.failure_count,
                "success_rate": round(grp.success_rate, 4),
            }
            for key, grp in groups.items()
        ],
    }
    return json.dumps(payload, indent=2)
