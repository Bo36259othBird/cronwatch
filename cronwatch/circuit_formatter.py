"""Format CircuitState objects as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_circuit_breaker import CircuitState


def _fmt_dt(dt) -> str:
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _state_to_dict(state: CircuitState) -> dict:
    return {
        "job_name": state.job_name,
        "is_open": state.is_open,
        "failure_count": state.failure_count,
        "total_count": state.total_count,
        "failure_rate": round(state.failure_rate, 4),
        "threshold": state.threshold,
        "tripped_at": _fmt_dt(state.tripped_at),
    }


def _as_text(states: List[CircuitState]) -> str:
    if not states:
        return "No circuit data available.\n"
    lines = ["Circuit Breaker Status", "=" * 40]
    for s in states:
        status = "OPEN (tripped)" if s.is_open else "closed"
        lines.append(
            f"  {s.job_name}: {status} "
            f"[{s.failure_count}/{s.total_count} failures, "
            f"rate={s.failure_rate:.0%}, threshold={s.threshold:.0%}]"
        )
        if s.tripped_at:
            lines.append(f"    tripped at: {_fmt_dt(s.tripped_at)}")
    return "\n".join(lines) + "\n"


def _as_json(states: List[CircuitState]) -> str:
    return json.dumps([_state_to_dict(s) for s in states], indent=2)


def format_circuits(
    states: List[CircuitState], fmt: str = "text"
) -> str:
    """Render *states* as *fmt* (``'text'`` or ``'json'``)."""
    if fmt == "json":
        return _as_json(states)
    return _as_text(states)
