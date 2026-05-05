"""Formats Report objects as plain-text or JSON strings."""

import json
from typing import Literal

from cronwatch.reporter import Report


def format_report(report: Report, fmt: Literal["text", "json"] = "text") -> str:
    if fmt == "json":
        return _as_json(report)
    return _as_text(report)


def _as_text(report: Report) -> str:
    lines = [
        f"CronWatch Report — {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Period: last {report.period_hours}h  |  Jobs tracked: {len(report.summaries)}",
        "-" * 60,
    ]
    for s in report.summaries:
        last = s.last_run_at.strftime("%Y-%m-%d %H:%M:%S") if s.last_run_at else "never"
        avg = f"{s.avg_duration_seconds:.1f}s" if s.avg_duration_seconds is not None else "n/a"
        lines.append(
            f"{s.job_name:<30} runs={s.total_runs:>4}  "
            f"ok={s.successful_runs:>4}  fail={s.failed_runs:>4}  "
            f"avg={avg:>8}  last={last}"
        )
    lines.append("-" * 60)
    lines.append(f"Total failures: {report.total_failures}")
    return "\n".join(lines)


def _as_json(report: Report) -> str:
    data = {
        "generated_at": report.generated_at.isoformat(),
        "period_hours": report.period_hours,
        "total_failures": report.total_failures,
        "jobs": [
            {
                "job_name": s.job_name,
                "total_runs": s.total_runs,
                "successful_runs": s.successful_runs,
                "failed_runs": s.failed_runs,
                "success_rate": round(s.success_rate, 2),
                "avg_duration_seconds": s.avg_duration_seconds,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "last_exit_code": s.last_exit_code,
            }
            for s in report.summaries
        ],
    }
    return json.dumps(data, indent=2)
