"""Format RunProfile objects as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_profiler import RunProfile


def _fmt(value: float | None, unit: str = "s") -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}{unit}"


def _profile_to_dict(p: RunProfile) -> dict:
    return {
        "job_name": p.job_name,
        "run_count": p.run_count,
        "p50_s": p.p50,
        "p95_s": p.p95,
        "p99_s": p.p99,
        "mean_s": p.mean,
        "stddev_s": p.stddev,
    }


def _as_text(profiles: List[RunProfile]) -> str:
    lines = ["Run Profiles", "============"]
    for p in profiles:
        lines.append(f"\nJob : {p.job_name}")
        lines.append(f"  Runs  : {p.run_count}")
        lines.append(f"  p50   : {_fmt(p.p50)}")
        lines.append(f"  p95   : {_fmt(p.p95)}")
        lines.append(f"  p99   : {_fmt(p.p99)}")
        lines.append(f"  mean  : {_fmt(p.mean)}")
        lines.append(f"  stddev: {_fmt(p.stddev)}")
    return "\n".join(lines)


def _as_json(profiles: List[RunProfile]) -> str:
    return json.dumps([_profile_to_dict(p) for p in profiles], indent=2)


def format_profiles(profiles: List[RunProfile], fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(profiles)
    return _as_text(profiles)
