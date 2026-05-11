"""Format :class:`RunPlan` objects for human and machine consumption."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from cronwatch.run_planner import RunPlan

_DATE_FMT = "%Y-%m-%d %H:%M:%S UTC"


def _fmt_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        return "N/A"
    return dt.strftime(_DATE_FMT)


def _fmt_seconds(s: Optional[float]) -> str:
    if s is None:
        return "N/A"
    if s < 0:
        return "overdue"
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {sec}s"
    return f"{sec}s"


def _plan_to_dict(plan: RunPlan) -> dict:
    return {
        "job_name": plan.job_name,
        "last_run": _fmt_dt(plan.last_run),
        "next_expected": _fmt_dt(plan.next_expected),
        "is_overdue": plan.is_overdue,
        "seconds_until_due": plan.seconds_until_due,
    }


def _as_text(plans: list[RunPlan]) -> str:
    lines = ["Run Planner", "=" * 40]
    for p in plans:
        status = "OVERDUE" if p.is_overdue else "ok"
        lines.append(f"  {p.job_name}")
        lines.append(f"    Last run    : {_fmt_dt(p.last_run)}")
        lines.append(f"    Next due    : {_fmt_dt(p.next_expected)}")
        lines.append(f"    Time until  : {_fmt_seconds(p.seconds_until_due)}")
        lines.append(f"    Status      : {status}")
    return "\n".join(lines)


def _as_json(plans: list[RunPlan]) -> str:
    return json.dumps([_plan_to_dict(p) for p in plans], indent=2)


def format_plans(plans: list[RunPlan], fmt: str = "text") -> str:
    """Return *plans* formatted as *fmt* (``'text'`` or ``'json'``)."""
    if fmt == "json":
        return _as_json(plans)
    return _as_text(plans)
