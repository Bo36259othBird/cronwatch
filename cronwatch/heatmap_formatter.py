"""Text and JSON formatters for RunHeatmap."""
from __future__ import annotations

import json
from typing import List

from cronwatch.run_heatmap import DAYS, HOURS, RunHeatmap


def format_heatmap(heatmap: RunHeatmap, fmt: str = "text") -> str:
    if fmt == "json":
        return _as_json(heatmap)
    return _as_text(heatmap)


def _as_text(heatmap: RunHeatmap) -> str:
    lines: List[str] = []
    lines.append(f"Heatmap: {heatmap.job_name}")
    lines.append("=" * 60)
    # Header row: hours
    hour_labels = "".join(f"{h:>3}" for h in HOURS)
    lines.append(f"{'':>4}{hour_labels}")
    for d in range(7):
        row_parts = []
        for h in HOURS:
            cell = heatmap.cell(d, h)
            row_parts.append(f"{cell.count:>3}")
        lines.append(f"{DAYS[d]:>4}{''.join(row_parts)}")
    peak = heatmap.peak_hour()
    if peak is not None:
        lines.append(f"Peak hour: {peak:02d}:00")
    return "\n".join(lines)


def _as_json(heatmap: RunHeatmap) -> str:
    cells = [
        {
            "day": DAYS[c.day],
            "hour": c.hour,
            "count": c.count,
            "failure_count": c.failure_count,
            "failure_rate": c.failure_rate,
        }
        for c in heatmap.cells
    ]
    payload = {
        "job_name": heatmap.job_name,
        "peak_hour": heatmap.peak_hour(),
        "cells": cells,
    }
    return json.dumps(payload, indent=2)
