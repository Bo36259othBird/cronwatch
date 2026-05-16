"""Track dependencies between cron jobs and detect ordering violations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.store import JobStore, JobRun


@dataclass
class DependencyViolation:
    job_name: str
    depends_on: str
    last_dependent_run_id: int
    blocking_run_id: Optional[int]
    message: str

    @property
    def is_blocking(self) -> bool:
        return self.blocking_run_id is not None


@dataclass
class DependencyGraph:
    """Maps job_name -> list of job names that must succeed before it runs."""
    edges: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, job: str, depends_on: str) -> None:
        self.edges.setdefault(job, []).append(depends_on)

    def dependencies(self, job: str) -> List[str]:
        return self.edges.get(job, [])


class RunDependencyChecker:
    """Check whether a job's declared dependencies have completed successfully."""

    def __init__(self, store: JobStore, graph: DependencyGraph) -> None:
        self._store = store
        self._graph = graph

    def check(self, job_name: str) -> List[DependencyViolation]:
        """Return violations for any unsatisfied dependency of *job_name*."""
        violations: List[DependencyViolation] = []
        last_run = self._store.get_last_run(job_name)
        if last_run is None:
            return violations

        for dep in self._graph.dependencies(job_name):
            dep_run = self._store.get_last_run(dep)
            if dep_run is None:
                violations.append(
                    DependencyViolation(
                        job_name=job_name,
                        depends_on=dep,
                        last_dependent_run_id=last_run.id,
                        blocking_run_id=None,
                        message=f"Dependency '{dep}' has never run.",
                    )
                )
                continue

            if dep_run.exit_code != 0 or dep_run.finished_at is None:
                violations.append(
                    DependencyViolation(
                        job_name=job_name,
                        depends_on=dep,
                        last_dependent_run_id=last_run.id,
                        blocking_run_id=dep_run.id,
                        message=(
                            f"Dependency '{dep}' last run (id={dep_run.id}) "
                            "did not complete successfully."
                        ),
                    )
                )
        return violations

    def all_violations(self, job_names: List[str]) -> Dict[str, List[DependencyViolation]]:
        return {job: self.check(job) for job in job_names}
