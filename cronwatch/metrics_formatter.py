"""Format a MetricsReport as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.metrics import MetricsReport


def format_metrics(report: MetricsReport, fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(report)
    return _as_text(report)


def _as_text(report: MetricsReport) -> str:
    lines: List[str] = ["=== Job Metrics ==="]
    if not report.jobs:
        lines.append("No data available.")
        return "\n".join(lines)

    for m in report.jobs:
        lines.append(f"\nJob: {m.job_name}")
        lines.append(f"  Runs       : {m.total_runs}")
        lines.append(f"  Successful : {m.successful_runs}")
        lines.append(f"  Failed     : {m.failed_runs}")
        lines.append(f"  Success %  : {m.success_rate * 100:.1f}%")
        if m.avg_duration_seconds is not None:
            lines.append(f"  Avg dur(s) : {m.avg_duration_seconds:.2f}")
            lines.append(f"  Min dur(s) : {m.min_duration_seconds:.2f}")
            lines.append(f"  Max dur(s) : {m.max_duration_seconds:.2f}")
        else:
            lines.append("  Duration   : n/a")
    return "\n".join(lines)


def _as_json(report: MetricsReport) -> str:
    data = []
    for m in report.jobs:
        data.append(
            {
                "job_name": m.job_name,
                "total_runs": m.total_runs,
                "successful_runs": m.successful_runs,
                "failed_runs": m.failed_runs,
                "success_rate": round(m.success_rate, 4),
                "avg_duration_seconds": m.avg_duration_seconds,
                "min_duration_seconds": m.min_duration_seconds,
                "max_duration_seconds": m.max_duration_seconds,
            }
        )
    return json.dumps({"metrics": data}, indent=2)
