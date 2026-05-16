"""Format MirrorResult for display."""
from __future__ import annotations

import json
from typing import Literal

from cronwatch.run_mirror import MirrorResult


def _pct(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "n/a"


def _result_to_dict(result: MirrorResult) -> dict:
    return {
        "job_a": result.job_a,
        "job_b": result.job_b,
        "runs_a": result.runs_a,
        "runs_b": result.runs_b,
        "failures_a": result.failures_a,
        "failures_b": result.failures_b,
        "success_rate_a": _pct(result.success_rate_a * 100 if result.success_rate_a is not None else None),
        "success_rate_b": _pct(result.success_rate_b * 100 if result.success_rate_b is not None else None),
        "diverged": result.diverged,
        "divergence_pct": result.divergence_pct,
    }


def _as_text(result: MirrorResult) -> str:
    lines = [
        "Mirror Comparison",
        "==================",
        f"Job A : {result.job_a}  ({result.runs_a} runs, {result.failures_a} failures)",
        f"Job B : {result.job_b}  ({result.runs_b} runs, {result.failures_b} failures)",
        f"Divergence : {_pct(result.divergence_pct)}",
        f"Diverged   : {'YES' if result.diverged else 'no'}",
    ]
    return "\n".join(lines)


def _as_json(result: MirrorResult) -> str:
    return json.dumps(_result_to_dict(result), indent=2)


def format_mirror(result: MirrorResult, fmt: Literal["text", "json"] = "text") -> str:
    if fmt == "json":
        return _as_json(result)
    return _as_text(result)
