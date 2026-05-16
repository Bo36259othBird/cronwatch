"""Formatters for ReplayCandidate output."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_replay import ReplayCandidate


def _fmt_dt(dt) -> str:
    if dt is None:
        return "n/a"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _candidate_to_dict(c: ReplayCandidate) -> dict:
    return {
        "job_name": c.job_name,
        "run_id": c.run_id,
        "started_at": _fmt_dt(c.started_at),
        "exit_code": c.exit_code,
        "reason": c.reason,
    }


def _as_text(candidates: List[ReplayCandidate]) -> str:
    if not candidates:
        return "No replay candidates found.\n"
    lines = ["Replay Candidates", "=" * 40]
    for c in candidates:
        lines.append(
            f"  run_id={c.run_id}  job={c.job_name}  "
            f"started={_fmt_dt(c.started_at)}  "
            f"exit_code={c.exit_code}  reason={c.reason}"
        )
    lines.append("")
    return "\n".join(lines)


def _as_json(candidates: List[ReplayCandidate]) -> str:
    return json.dumps([_candidate_to_dict(c) for c in candidates], indent=2)


def format_replay(
    candidates: List[ReplayCandidate], fmt: str = "text"
) -> str:
    if fmt == "json":
        return _as_json(candidates)
    return _as_text(candidates)
