"""Format EscalationLevel results as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_escalator import EscalationLevel

_DT_FMT = "%Y-%m-%d %H:%M:%S UTC"


def _fmt_dt(dt) -> str:
    return dt.strftime(_DT_FMT) if dt else "n/a"


def _level_to_dict(lvl: EscalationLevel) -> dict:
    return {
        "job": lvl.job_name,
        "level": lvl.level,
        "label": lvl.label,
        "consecutive_failures": lvl.consecutive_failures,
        "first_failure_at": _fmt_dt(lvl.first_failure_at),
        "last_failure_at": _fmt_dt(lvl.last_failure_at),
    }


def _as_text(levels: List[EscalationLevel]) -> str:
    if not levels:
        return "No escalation data.\n"
    lines = ["Escalation Report", "=" * 40]
    for lvl in levels:
        indicator = "[!!]" if lvl.level == 2 else "[!] " if lvl.level == 1 else "[ok]"
        lines.append(
            f"{indicator} {lvl.job_name}: {lvl.label} "
            f"({lvl.consecutive_failures} consecutive failure(s))"
        )
        if lvl.is_elevated:
            lines.append(f"      first: {_fmt_dt(lvl.first_failure_at)}")
            lines.append(f"      last:  {_fmt_dt(lvl.last_failure_at)}")
    return "\n".join(lines) + "\n"


def _as_json(levels: List[EscalationLevel]) -> str:
    return json.dumps([_level_to_dict(lvl) for lvl in levels], indent=2)


def format_escalation(levels: List[EscalationLevel], fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(levels)
    return _as_text(levels)
