"""Format Baseline objects as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_baseline import Baseline


def _fmt(value: float | None, unit: str = "s") -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}{unit}"


def _baseline_to_dict(b: Baseline) -> dict:
    return {
        "job_name": b.job_name,
        "sample_size": b.sample_size,
        "mean_duration": b.mean_duration,
        "std_duration": b.std_duration,
        "lower_bound": b.lower_bound,
        "upper_bound": b.upper_bound,
    }


def _as_text(baselines: List[Baseline]) -> str:
    if not baselines:
        return "No baseline data available.\n"
    lines = ["Job Baselines", "=" * 50]
    for b in baselines:
        lines.append(f"Job       : {b.job_name}")
        lines.append(f"Samples   : {b.sample_size}")
        lines.append(f"Mean      : {_fmt(b.mean_duration)}")
        lines.append(f"Std Dev   : {_fmt(b.std_duration)}")
        lines.append(f"Window    : [{_fmt(b.lower_bound)}, {_fmt(b.upper_bound)}]")
        lines.append("-" * 50)
    return "\n".join(lines) + "\n"


def _as_json(baselines: List[Baseline]) -> str:
    return json.dumps([_baseline_to_dict(b) for b in baselines], indent=2)


def format_baselines(baselines: List[Baseline], fmt: str = "text") -> str:
    """Return *baselines* formatted as *fmt* (``'text'`` or ``'json'``)."""
    if fmt == "json":
        return _as_json(baselines)
    return _as_text(baselines)
