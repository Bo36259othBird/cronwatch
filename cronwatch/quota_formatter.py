"""Formatters for QuotaResult objects."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_quota import QuotaResult


def _result_to_dict(r: QuotaResult) -> dict:
    return {
        "job_name": r.job_name,
        "window_seconds": r.window_seconds,
        "limit": r.limit,
        "actual": r.actual,
        "exceeded": r.exceeded,
        "excess": r.excess,
        "utilisation": round(r.utilisation, 4),
    }


def _as_text(results: List[QuotaResult]) -> str:
    if not results:
        return "No quota results.\n"
    lines = ["Run Quota Report", "=" * 40]
    for r in results:
        status = "EXCEEDED" if r.exceeded else "OK"
        lines.append(
            f"  {r.job_name}: {r.actual}/{r.limit} in {r.window_seconds}s "
            f"[{status}]" + (f" (+{r.excess} over)" if r.exceeded else "")
        )
    lines.append("")
    return "\n".join(lines)


def _as_json(results: List[QuotaResult]) -> str:
    return json.dumps([_result_to_dict(r) for r in results], indent=2)


def format_quota(results: List[QuotaResult], fmt: str = "text") -> str:
    """Format *results* as *fmt* (``'text'`` or ``'json'``)."""
    if fmt == "json":
        return _as_json(results)
    return _as_text(results)
