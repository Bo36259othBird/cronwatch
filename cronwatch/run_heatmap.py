"""Builds a heatmap of job run counts bucketed by hour-of-day and day-of-week."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.store import JobStore

# day index: 0=Monday … 6=Sunday  (matches datetime.weekday())
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = list(range(24))


@dataclass
class HeatmapCell:
    day: int        # 0-6
    hour: int       # 0-23
    count: int = 0
    failure_count: int = 0

    @property
    def failure_rate(self) -> Optional[float]:
        if self.count == 0:
            return None
        return self.failure_count / self.count


@dataclass
class RunHeatmap:
    job_name: str
    cells: List[HeatmapCell] = field(default_factory=list)

    def cell(self, day: int, hour: int) -> HeatmapCell:
        for c in self.cells:
            if c.day == day and c.hour == hour:
                return c
        raise KeyError(f"No cell for day={day} hour={hour}")

    def peak_hour(self) -> Optional[int]:
        """Return the hour (0-23) with the highest total run count."""
        if not self.cells:
            return None
        return max(self.cells, key=lambda c: c.count).hour


class RunHeatmapBuilder:
    def __init__(self, store: JobStore) -> None:
        self._store = store

    def build(self, job_name: str) -> RunHeatmap:
        heatmap = RunHeatmap(job_name=job_name)
        # Pre-populate all 7x24 cells
        grid: Dict[tuple, HeatmapCell] = {}
        for d in range(7):
            for h in HOURS:
                cell = HeatmapCell(day=d, hour=h)
                grid[(d, h)] = cell
                heatmap.cells.append(cell)

        runs = self._store.get_runs(job_name)
        for run in runs:
            ts = run.started_at
            key = (ts.weekday(), ts.hour)
            cell = grid[key]
            cell.count += 1
            if run.exit_code is not None and run.exit_code != 0:
                cell.failure_count += 1

        return heatmap
