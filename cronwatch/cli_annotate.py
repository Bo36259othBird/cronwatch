"""CLI sub-commands for managing run annotations."""
from __future__ import annotations

import argparse
import sys
import json

from cronwatch.config import load_config
from cronwatch.store import JobStore
from cronwatch.run_annotator import RunAnnotator


def add_annotate_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("annotate", help="manage run annotations")
    cmds = p.add_subparsers(dest="annotate_cmd")

    # set
    s = cmds.add_parser("set", help="attach a key=value annotation to a run")
    s.add_argument("run_id", type=int)
    s.add_argument("key")
    s.add_argument("value")

    # get
    g = cmds.add_parser("get", help="list annotations for a run")
    g.add_argument("run_id", type=int)
    g.add_argument("--format", dest="fmt", choices=["text", "json"], default="text")

    # delete
    d = cmds.add_parser("delete", help="remove a single annotation")
    d.add_argument("run_id", type=int)
    d.add_argument("key")


def cmd_annotate(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config not found: {args.config}", file=sys.stderr)
        return 2

    store = JobStore(cfg.db_path)
    annotator = RunAnnotator(store)

    sub = getattr(args, "annotate_cmd", None)
    if sub == "set":
        annotator.annotate(args.run_id, args.key, args.value)
        print(f"Annotation '{args.key}' set on run {args.run_id}.")
        return 0

    if sub == "get":
        data = annotator.get(args.run_id)
        if getattr(args, "fmt", "text") == "json":
            print(json.dumps({"run_id": args.run_id, "annotations": data}))
        else:
            if not data:
                print(f"No annotations for run {args.run_id}.")
            else:
                for k, v in sorted(data.items()):
                    print(f"  {k}: {v}")
        return 0

    if sub == "delete":
        removed = annotator.delete(args.run_id, args.key)
        if removed:
            print(f"Annotation '{args.key}' removed from run {args.run_id}.")
        else:
            print(f"No annotation '{args.key}' found on run {args.run_id}.")
        return 0

    print("Specify a sub-command: set | get | delete", file=sys.stderr)
    return 1
