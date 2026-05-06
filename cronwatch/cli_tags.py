"""CLI sub-commands for tag-based job inspection."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.tags import TagIndex


def add_tags_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tags", help="inspect jobs by tag")
    p.add_argument("--config", required=True, help="path to cronwatch config file")
    sub = p.add_subparsers(dest="tags_cmd")

    ls = sub.add_parser("list", help="list all tags")
    ls.add_argument("--config")  # inherited; ignored here

    show = sub.add_parser("show", help="show jobs for a tag")
    show.add_argument("tag", help="tag name")


def cmd_tags(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    index = TagIndex(config)
    sub = getattr(args, "tags_cmd", None)

    if sub == "show":
        group = index.group(args.tag)
        if group is None:
            print(f"No jobs found for tag '{args.tag}'", file=sys.stderr)
            return 1
        print(f"Tag: {group.tag}")
        for name in group.job_names:
            print(f"  - {name}")
        return 0

    # default: list all tags
    all_tags = index.tags()
    if not all_tags:
        print("No tags defined.")
    else:
        for tag in all_tags:
            jobs = index.jobs_for_tag(tag)
            print(f"{tag} ({len(jobs)} job{'s' if len(jobs) != 1 else ''})")
    return 0
