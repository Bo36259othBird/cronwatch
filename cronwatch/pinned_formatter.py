"""Format pinned run results as text or JSON."""
from __future__ import annotations

import json
from typing import Literal

from cronwatch.run_pinned import PinnedRun


def _pin_to_dict(pin: PinnedRun) -> dict:
    return {
        "job_name": pin.job_name,
        "run_id": pin.run_id,
        "reason": pin.reason,
        "duration_seconds": round(pin.duration, 3) if pin.duration is not None else None,
    }


def _as_text(pins: list[PinnedRun]) -> str:
    if not pins:
        return "No pinned runs found.\n"
    lines = ["Pinned Runs", "=" * 40]
    for pin in pins:
        dur = f"{pin.duration:.3f}s" if pin.duration is not None else "N/A"
        flag = "  [!]" if pin.is_failure() else ""
        lines.append(
            f"  [{pin.reason}] run_id={pin.run_id}  job={pin.job_name}  duration={dur}{flag}"
        )
    lines.append("")
    return "\n".join(lines)


def _as_json(pins: list[PinnedRun]) -> str:
    return json.dumps([_pin_to_dict(p) for p in pins], indent=2)


def format_pins(
    pins: list[PinnedRun],
    fmt: Literal["text", "json"] = "text",
) -> str:
    if fmt == "json":
        return _as_json(pins)
    return _as_text(pins)
