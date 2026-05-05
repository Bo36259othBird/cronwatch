"""Format history/trend data for human or machine consumption."""
from __future__ import annotations

import json
from typing import List

from cronwatch.history import JobTrend

_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def format_trends(trends: List[JobTrend], fmt: str = "text") -> str:
    if fmt == "json":
        return _trends_as_json(trends)
    return _trends_as_text(trends)


def _trends_as_text(trends: List[JobTrend]) -> str:
    if not trends:
        return "No trend data available.\n"

    lines = ["Job History Trends", "=" * 40]
    for t in trends:
        last = t.last_run_at.strftime(_DATE_FMT) if t.last_run_at else "never"
        avg = f"{t.avg_duration_seconds:.1f}s" if t.avg_duration_seconds is not None else "n/a"
        flag = "  [DEGRADING]" if t.is_degrading else ""
        lines.append(
            f"{t.job_name} (last {t.window_days}d){flag}\n"
            f"  runs={t.total_runs}  ok={t.successful_runs}  fail={t.failed_runs}"
            f"  failure_rate={t.failure_rate:.0%}  avg_dur={avg}  last={last}"
        )
    return "\n".join(lines) + "\n"


def _trends_as_json(trends: List[JobTrend]) -> str:
    payload = []
    for t in trends:
        payload.append({
            "job_name": t.job_name,
            "window_days": t.window_days,
            "total_runs": t.total_runs,
            "successful_runs": t.successful_runs,
            "failed_runs": t.failed_runs,
            "failure_rate": round(t.failure_rate, 4),
            "avg_duration_seconds": t.avg_duration_seconds,
            "last_run_at": t.last_run_at.strftime(_DATE_FMT) if t.last_run_at else None,
            "is_degrading": t.is_degrading,
        })
    return json.dumps(payload, indent=2)
