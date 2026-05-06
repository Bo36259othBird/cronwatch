"""Rate limiter to prevent alert flooding for repeated failures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


@dataclass
class _Entry:
    first_seen: datetime
    last_sent: datetime
    count: int = 1


@dataclass
class RateLimiter:
    """Suppress duplicate alerts within a cooldown window."""

    cooldown_seconds: int = 300
    _state: Dict[str, _Entry] = field(default_factory=dict, init=False, repr=False)

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def should_send(self, key: str) -> bool:
        """Return True if an alert for *key* should be sent right now."""
        now = self._now()
        entry = self._state.get(key)
        if entry is None:
            self._state[key] = _Entry(first_seen=now, last_sent=now)
            return True
        elapsed = (now - entry.last_sent).total_seconds()
        if elapsed >= self.cooldown_seconds:
            entry.last_sent = now
            entry.count += 1
            return True
        return False

    def reset(self, key: str) -> None:
        """Clear rate-limit state for *key* (e.g. after recovery)."""
        self._state.pop(key, None)

    def get_count(self, key: str) -> int:
        """Return how many alerts have been sent for *key*."""
        entry = self._state.get(key)
        return entry.count if entry else 0

    def next_allowed(self, key: str) -> Optional[datetime]:
        """Return the earliest datetime the next alert for *key* is allowed."""
        entry = self._state.get(key)
        if entry is None:
            return None
        return entry.last_sent + timedelta(seconds=self.cooldown_seconds)
