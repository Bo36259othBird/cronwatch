"""CLI sub-command for checking job dependency violations."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.store import JobStore
from cronwatch.run_dependency import DependencyGraph, RunDependencyChecker
from cronwatch.dependency_formatter import format_dependencies


def add_dependency_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("dependency", help="Check job dependency violations")
    p.add_argument("--config", required=True, help="Path to cronwatch config file")
    p.add_argument(
        "--format", choices=["text", "json"], default="text", dest="fmt"
    )
    p.set_defaults(func=cmd_dependency)


def cmd_dependency(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    graph = DependencyGraph()
    for job in cfg.jobs:
        for dep in getattr(job, "depends_on", []) or []:
            graph.add(job.name, dep)

    store = JobStore()
    checker = RunDependencyChecker(store, graph)
    job_names = [j.name for j in cfg.jobs]
    results = checker.all_violations(job_names)

    print(format_dependencies(results, fmt=args.fmt))

    any_violations = any(v for vs in results.values() for v in vs)
    return 1 if any_violations else 0
