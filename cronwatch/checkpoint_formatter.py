"""Format checkpoint summaries as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_checkpoint import CheckpointSummary


def _fmt_dt(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"


def _summary_to_dict(summary: CheckpointSummary) -> dict:
    return {
        "run_id": summary.run_id,
        "job_name": summary.job_name,
        "checkpoint_count": summary.count,
        "checkpoints": [
            {
                "name": c.name,
                "reached_at": _fmt_dt(c.reached_at),
                "metadata": c.metadata,
            }
            for c in summary.checkpoints
        ],
    }


def _as_text(summaries: List[CheckpointSummary]) -> str:
    if not summaries:
        return "No checkpoints recorded.\n"
    lines = ["Checkpoint Report", "=" * 40]
    for s in summaries:
        lines.append(f"Run #{s.run_id}  job={s.job_name}  checkpoints={s.count}")
        if s.checkpoints:
            for c in s.checkpoints:
                meta_str = f"  meta={c.metadata}" if c.metadata else ""
                lines.append(f"  [{_fmt_dt(c.reached_at)}] {c.name}{meta_str}")
        else:
            lines.append("  (none)")
    lines.append("")
    return "\n".join(lines)


def _as_json(summaries: List[CheckpointSummary]) -> str:
    return json.dumps([_summary_to_dict(s) for s in summaries], indent=2)


def format_checkpoints(summaries: List[CheckpointSummary], fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(summaries)
    return _as_text(summaries)
