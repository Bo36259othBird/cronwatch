"""Format dependency violation results as text or JSON."""
from __future__ import annotations

import json
from typing import Dict, List

from cronwatch.run_dependency import DependencyViolation


def _violation_to_dict(v: DependencyViolation) -> dict:
    return {
        "job_name": v.job_name,
        "depends_on": v.depends_on,
        "last_dependent_run_id": v.last_dependent_run_id,
        "blocking_run_id": v.blocking_run_id,
        "is_blocking": v.is_blocking,
        "message": v.message,
    }


def _as_text(violations_by_job: Dict[str, List[DependencyViolation]]) -> str:
    lines = ["=== Dependency Violations ==="]
    any_found = False
    for job, violations in violations_by_job.items():
        if not violations:
            continue
        any_found = True
        lines.append(f"\nJob: {job}")
        for v in violations:
            blocking = f" (blocking run {v.blocking_run_id})" if v.is_blocking else ""
            lines.append(f"  - depends_on={v.depends_on}{blocking}: {v.message}")
    if not any_found:
        lines.append("  No violations detected.")
    return "\n".join(lines)


def _as_json(violations_by_job: Dict[str, List[DependencyViolation]]) -> str:
    payload = {
        job: [_violation_to_dict(v) for v in violations]
        for job, violations in violations_by_job.items()
    }
    return json.dumps(payload, indent=2)


def format_dependencies(
    violations_by_job: Dict[str, List[DependencyViolation]],
    fmt: str = "text",
) -> str:
    if fmt == "json":
        return _as_json(violations_by_job)
    return _as_text(violations_by_job)
