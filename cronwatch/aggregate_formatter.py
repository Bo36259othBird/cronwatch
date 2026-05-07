"""Format AggregateReport as text or JSON."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from cronwatch.run_aggregator import AggregateReport, JobAggregate


def _fmt_dur(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    return f"{seconds:.2f}s"


def _aggregate_to_dict(agg: JobAggregate) -> Dict[str, Any]:
    return {
        "job_name": agg.job_name,
        "total_runs": agg.total_runs,
        "successful_runs": agg.successful_runs,
        "failed_runs": agg.failed_runs,
        "success_rate": round(agg.success_rate, 4),
        "avg_duration_seconds": agg.avg_duration_seconds,
        "max_duration_seconds": agg.max_duration_seconds,
        "min_duration_seconds": agg.min_duration_seconds,
    }


def _as_text(report: AggregateReport) -> str:
    lines = [
        "=== Run Aggregate Report ===",
        f"Jobs: {report.total_jobs}  "
        f"Total runs: {report.total_runs}  "
        f"Total failures: {report.total_failures}",
        "",
    ]
    for agg in report.aggregates:
        lines.append(f"[{agg.job_name}]")
        lines.append(f"  Runs      : {agg.total_runs}")
        lines.append(f"  Successes : {agg.successful_runs}")
        lines.append(f"  Failures  : {agg.failed_runs}")
        lines.append(f"  Success % : {agg.success_rate * 100:.1f}%")
        lines.append(f"  Avg dur   : {_fmt_dur(agg.avg_duration_seconds)}")
        lines.append(f"  Min dur   : {_fmt_dur(agg.min_duration_seconds)}")
        lines.append(f"  Max dur   : {_fmt_dur(agg.max_duration_seconds)}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _as_json(report: AggregateReport) -> str:
    payload = {
        "total_jobs": report.total_jobs,
        "total_runs": report.total_runs,
        "total_failures": report.total_failures,
        "aggregates": [_aggregate_to_dict(a) for a in report.aggregates],
    }
    return json.dumps(payload, indent=2)


def format_aggregate(report: AggregateReport, fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(report)
    return _as_text(report)
