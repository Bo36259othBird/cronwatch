"""Dispatch run events to registered handlers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from cronwatch.store import JobRun


@dataclass
class DispatchEvent:
    """An event emitted when a run transitions state."""

    kind: str  # 'started' | 'finished' | 'failed'
    job_name: str
    run_id: int
    run: JobRun


Handler = Callable[[DispatchEvent], None]


class RunDispatcher:
    """Maintains a registry of handlers and dispatches run lifecycle events."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = {
            "started": [],
            "finished": [],
            "failed": [],
        }

    def register(self, kind: str, handler: Handler) -> None:
        """Register *handler* for events of *kind*.

        Raises ValueError for unknown event kinds.
        """
        if kind not in self._handlers:
            raise ValueError(f"Unknown event kind: {kind!r}")
        self._handlers[kind].append(handler)

    def dispatch(self, event: DispatchEvent) -> None:
        """Call all handlers registered for *event.kind*."""
        for handler in self._handlers.get(event.kind, []):
            handler(event)

    def dispatch_started(self, run: JobRun) -> None:
        """Convenience method to dispatch a 'started' event."""
        self.dispatch(
            DispatchEvent(kind="started", job_name=run.job_name, run_id=run.run_id, run=run)
        )

    def dispatch_finished(self, run: JobRun) -> None:
        """Convenience method to dispatch a 'finished' or 'failed' event."""
        kind = "failed" if run.exit_code != 0 else "finished"
        self.dispatch(
            DispatchEvent(kind=kind, job_name=run.job_name, run_id=run.run_id, run=run)
        )

    def handler_count(self, kind: str) -> int:
        """Return the number of handlers registered for *kind*."""
        return len(self._handlers.get(kind, []))
