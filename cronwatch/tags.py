"""Tag-based filtering and grouping for cron jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.config import CronwatchConfig, JobConfig


@dataclass
class TagGroup:
    """A named collection of jobs sharing a tag."""

    tag: str
    jobs: List[JobConfig] = field(default_factory=list)

    @property
    def job_names(self) -> List[str]:
        return [j.name for j in self.jobs]


class TagIndex:
    """Builds and queries an index of jobs by tag."""

    def __init__(self, config: CronwatchConfig) -> None:
        self._index: Dict[str, List[JobConfig]] = {}
        for job in config.jobs:
            for tag in getattr(job, "tags", []) or []:
                self._index.setdefault(tag, []).append(job)

    def tags(self) -> List[str]:
        """Return all known tags, sorted."""
        return sorted(self._index.keys())

    def jobs_for_tag(self, tag: str) -> List[JobConfig]:
        """Return jobs associated with *tag*, or empty list."""
        return list(self._index.get(tag, []))

    def group(self, tag: str) -> Optional[TagGroup]:
        """Return a TagGroup for *tag*, or None if tag is unknown."""
        jobs = self.jobs_for_tag(tag)
        if not jobs:
            return None
        return TagGroup(tag=tag, jobs=jobs)

    def all_groups(self) -> List[TagGroup]:
        """Return TagGroup for every known tag."""
        return [TagGroup(tag=t, jobs=self.jobs_for_tag(t)) for t in self.tags()]

    def jobs_matching_any(self, tags: List[str]) -> List[JobConfig]:
        """Return deduplicated jobs that have at least one of *tags*."""
        seen: set = set()
        result: List[JobConfig] = []
        for tag in tags:
            for job in self.jobs_for_tag(tag):
                if job.name not in seen:
                    seen.add(job.name)
                    result.append(job)
        return result
