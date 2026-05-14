"""Formatters for BudgetResult objects."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_budget import BudgetResult


def _fmt(seconds: float | None) -> str:
    if seconds is None:
        return "N/A"
    return f"{seconds:.2f}s"


def _result_to_dict(r: BudgetResult) -> dict:
    return {
        "job_name": r.job_name,
        "run_id": r.run_id,
        "budget_seconds": r.budget_seconds,
        "actual_seconds": r.actual_seconds,
        "exceeded": r.exceeded,
        "overage_seconds": r.overage_seconds,
    }


def _as_text(results: List[BudgetResult]) -> str:
    if not results:
        return "No budget results available.\n"

    lines = ["Run Budget Report", "=" * 40]
    for r in results:
        status = "EXCEEDED" if r.exceeded else "OK"
        line = (
            f"  {r.job_name} (run {r.run_id}): "
            f"{_fmt(r.actual_seconds)} / {_fmt(r.budget_seconds)} [{status}]"
        )
        if r.exceeded and r.overage_seconds is not None:
            line += f" (+{_fmt(r.overage_seconds)} over budget)"
        lines.append(line)
    return "\n".join(lines) + "\n"


def _as_json(results: List[BudgetResult]) -> str:
    return json.dumps([_result_to_dict(r) for r in results], indent=2)


def format_budget(
    results: List[BudgetResult], fmt: str = "text"
) -> str:
    """Format *results* as ``'text'`` or ``'json'``."""
    if fmt == "json":
        return _as_json(results)
    return _as_text(results)
