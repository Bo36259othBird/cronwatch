"""Formatters for RunLedger entries."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_ledger import LedgerEntry


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def _entry_to_dict(entry: LedgerEntry) -> dict:
    return {
        "job_name": entry.job_name,
        "total_runs": entry.total_runs,
        "total_successes": entry.total_successes,
        "total_failures": entry.total_failures,
        "success_rate": _pct(entry.success_rate),
        "first_run_at": entry.first_run_at,
        "last_run_at": entry.last_run_at,
    }


def _as_text(entries: List[LedgerEntry]) -> str:
    if not entries:
        return "Ledger: no entries.\n"
    lines = ["=== Run Ledger ==="]
    for e in entries:
        lines.append(
            f"  {e.job_name}: runs={e.total_runs} "
            f"ok={e.total_successes} fail={e.total_failures} "
            f"rate={_pct(e.success_rate)}"
        )
        if e.first_run_at:
            lines.append(f"    first={e.first_run_at}  last={e.last_run_at}")
    return "\n".join(lines) + "\n"


def _as_json(entries: List[LedgerEntry]) -> str:
    return json.dumps([_entry_to_dict(e) for e in entries], indent=2)


def format_ledger(entries: List[LedgerEntry], fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(entries)
    return _as_text(entries)
