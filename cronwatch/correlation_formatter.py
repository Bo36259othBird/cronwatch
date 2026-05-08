"""Format CorrelatedPair results as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_correlator import CorrelatedPair


def _pair_to_dict(pair: CorrelatedPair) -> dict:
    return {
        "job_a": pair.job_a,
        "job_b": pair.job_b,
        "overlap_count": pair.overlap_count,
        "co_failure_count": pair.co_failure_count,
        "co_failure_rate": round(pair.co_failure_rate, 4),
        "is_correlated": pair.is_correlated,
    }


def _as_text(pairs: List[CorrelatedPair]) -> str:
    if not pairs:
        return "No correlation data available.\n"

    lines = ["Job Correlation Report", "=" * 40]
    for p in pairs:
        flag = " [CORRELATED]" if p.is_correlated else ""
        lines.append(
            f"{p.job_a} <-> {p.job_b}{flag}\n"
            f"  overlapping runs : {p.overlap_count}\n"
            f"  co-failures      : {p.co_failure_count}\n"
            f"  co-failure rate  : {p.co_failure_rate:.1%}"
        )
    return "\n".join(lines) + "\n"


def _as_json(pairs: List[CorrelatedPair]) -> str:
    return json.dumps([_pair_to_dict(p) for p in pairs], indent=2)


def format_correlation(pairs: List[CorrelatedPair], fmt: str = "text") -> str:
    """Return formatted correlation output.

    Args:
        pairs: List of CorrelatedPair objects.
        fmt:   ``"text"`` (default) or ``"json"``.
    """
    if fmt == "json":
        return _as_json(pairs)
    return _as_text(pairs)
