"""Formats Streak objects for CLI output."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_streaker import Streak


def format_streak(streak: Streak, fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json([streak])
    return _as_text([streak])


def format_streaks(streaks: List[Streak], fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(streaks)
    return _as_text(streaks)


def _streak_to_dict(s: Streak) -> dict:
    return {
        "job": s.job_name,
        "kind": s.kind,
        "length": s.length,
        "is_active": s.is_active,
        "is_concerning": s.is_concerning,
    }


def _as_text(streaks: List[Streak]) -> str:
    if not streaks:
        return "No streak data available.\n"
    lines = ["Streak Report", "=" * 40]
    for s in streaks:
        flag = " [!]" if s.is_concerning else ""
        lines.append(
            f"  {s.job_name}: {s.kind.upper()} x{s.length}{flag}"
        )
    lines.append("")
    return "\n".join(lines)


def _as_json(streaks: List[Streak]) -> str:
    return json.dumps([_streak_to_dict(s) for s in streaks], indent=2)
