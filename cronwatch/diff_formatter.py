"""Format a :class:`RunDiff` as text or JSON."""
from __future__ import annotations

import json
from typing import Literal

from cronwatch.run_comparator import RunDiff


def format_diff(diff: RunDiff, fmt: Literal["text", "json"] = "text") -> str:
    """Return *diff* formatted as *fmt*.

    Parameters
    ----------
    diff:
        The :class:`RunDiff` object produced by :func:`~cronwatch.run_comparator.compare_runs`.
    fmt:
        Output format – ``"text"`` for a human-readable summary or ``"json"``
        for a machine-readable JSON string.

    Raises
    ------
    ValueError
        If *fmt* is not one of the supported format strings.
    """
    if fmt == "json":
        return _as_json(diff)
    if fmt == "text":
        return _as_text(diff)
    raise ValueError(f"Unsupported format {fmt!r}. Expected 'text' or 'json'.")


def _as_text(diff: RunDiff) -> str:
    lines = [
        f"Run comparison for job: {diff.job_name}",
        f"  Run A (id={diff.run_id_a})  ->  Run B (id={diff.run_id_b})",
    ]

    def _fmt_dur(d: float | None) -> str:
        return f"{d:.3f}s" if d is not None else "n/a"

    lines.append(f"  Duration : {_fmt_dur(diff.duration_a)} -> {_fmt_dur(diff.duration_b)}")

    if diff.duration_delta is not None:
        sign = "+" if diff.duration_delta >= 0 else ""
        lines.append(f"  Delta    : {sign}{diff.duration_delta:.3f}s")
        if diff.slower:
            lines.append("  Trend    : SLOWER")
        elif diff.faster:
            lines.append("  Trend    : FASTER")
        else:
            lines.append("  Trend    : UNCHANGED")

    lines.append(
        f"  Exit code: {diff.exit_code_a} -> {diff.exit_code_b}"
        + ("  [CHANGED]" if diff.status_changed else "")
    )
    return "\n".join(lines)


def _as_json(diff: RunDiff) -> str:
    return json.dumps(
        {
            "job_name": diff.job_name,
            "run_id_a": diff.run_id_a,
            "run_id_b": diff.run_id_b,
            "duration_a": diff.duration_a,
            "duration_b": diff.duration_b,
            "duration_delta": diff.duration_delta,
            "exit_code_a": diff.exit_code_a,
            "exit_code_b": diff.exit_code_b,
            "status_changed": diff.status_changed,
            "slower": diff.slower,
            "faster": diff.faster,
        },
        indent=2,
    )
