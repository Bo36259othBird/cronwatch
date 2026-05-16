"""Format DispatchEvent objects for display or logging."""
from __future__ import annotations

import json
from typing import Any, Dict

from cronwatch.run_dispatcher import DispatchEvent


def _event_to_dict(event: DispatchEvent) -> Dict[str, Any]:
    run = event.run
    return {
        "kind": event.kind,
        "job_name": event.job_name,
        "run_id": event.run_id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "exit_code": run.exit_code,
    }


def _as_text(event: DispatchEvent) -> str:
    d = _event_to_dict(event)
    lines = [
        f"Event      : {d['kind'].upper()}",
        f"Job        : {d['job_name']}",
        f"Run ID     : {d['run_id']}",
        f"Started    : {d['started_at'] or 'n/a'}",
        f"Finished   : {d['finished_at'] or 'n/a'}",
        f"Exit code  : {d['exit_code'] if d['exit_code'] is not None else 'n/a'}",
    ]
    return "\n".join(lines)


def _as_json(event: DispatchEvent) -> str:
    return json.dumps(_event_to_dict(event), indent=2)


def format_event(event: DispatchEvent, fmt: str = "text") -> str:
    """Return a formatted string for *event*.

    *fmt* is either ``'text'`` (default) or ``'json'``.
    """
    if fmt == "json":
        return _as_json(event)
    return _as_text(event)
