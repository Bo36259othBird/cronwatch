"""Formatters for SentinelAlert output."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_sentinel import SentinelAlert


def _fmt_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    return f"{minutes / 60:.1f}h"


def _fmt_dt(dt) -> str:
    if dt is None:
        return "never"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _alert_to_dict(alert: SentinelAlert) -> dict:
    return {
        "job_name": alert.job_name,
        "expected_interval_seconds": alert.expected_interval_seconds,
        "last_run_at": _fmt_dt(alert.last_run_at),
        "overdue_by_seconds": round(alert.overdue_by_seconds, 2),
        "never_run": alert.is_never_run,
    }


def _as_text(alerts: List[SentinelAlert]) -> str:
    if not alerts:
        return "sentinel: all jobs within expected cadence\n"
    lines = ["SENTINEL ALERTS", "=" * 40]
    for a in alerts:
        lines.append(f"job       : {a.job_name}")
        lines.append(f"last run  : {_fmt_dt(a.last_run_at)}")
        lines.append(f"interval  : {_fmt_seconds(a.expected_interval_seconds)}")
        lines.append(f"overdue by: {_fmt_seconds(a.overdue_by_seconds)}")
        lines.append("-" * 40)
    return "\n".join(lines) + "\n"


def _as_json(alerts: List[SentinelAlert]) -> str:
    return json.dumps([_alert_to_dict(a) for a in alerts], indent=2)


def format_sentinel(alerts: List[SentinelAlert], fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(alerts)
    return _as_text(alerts)
