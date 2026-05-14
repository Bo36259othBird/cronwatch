"""Format ThrottleViolation results as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_throttler import ThrottleViolation


def _fmt_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    return f"{minutes / 60:.1f}h"


def _violation_to_dict(v: ThrottleViolation) -> dict:
    return {
        "job_name": v.job_name,
        "run_id": v.run_id,
        "started_at": v.started_at.isoformat(),
        "previous_started_at": v.previous_started_at.isoformat(),
        "gap_seconds": round(v.gap_seconds, 3),
        "min_gap_seconds": v.min_gap_seconds,
        "is_violation": v.is_violation,
    }


def _as_text(violations: List[ThrottleViolation]) -> str:
    if not violations:
        return "No throttle violations found.\n"
    lines = ["Throttle Violations", "=" * 40]
    for v in violations:
        lines.append(
            f"  [{v.job_name}] run #{v.run_id}: "
            f"gap={_fmt_seconds(v.gap_seconds)} "
            f"(min={_fmt_seconds(v.min_gap_seconds)}) "
            f"at {v.started_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    lines.append(f"Total: {len(violations)} violation(s)")
    return "\n".join(lines) + "\n"


def _as_json(violations: List[ThrottleViolation]) -> str:
    return json.dumps([_violation_to_dict(v) for v in violations], indent=2)


def format_throttle(violations: List[ThrottleViolation], fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(violations)
    return _as_text(violations)
