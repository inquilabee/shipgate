"""Standalone CLI: check / fix / list."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from refactor.inventory import load_inventory
from refactor.registry import RULES
from refactor.runner import check_paths, fix_paths, hits_to_jsonable


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "list":
        return cmd_list()
    paths: list[Path] = list(args.paths) or [Path()]
    if args.command == "check":
        return cmd_check(paths)
    if args.command == "fix":
        return cmd_fix(paths)
    return 2


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="refactor")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List registered rules")
    check_parser = sub.add_parser("check", help="Detect issues and print JSON hits")
    check_parser.add_argument("paths", nargs="*", type=Path, default=[Path()])
    fix_parser = sub.add_parser("fix", help="Apply safe_apply rules")
    fix_parser.add_argument("paths", nargs="*", type=Path, default=[Path()])
    return parser.parse_args(argv)


def cmd_list() -> int:
    status_by_id = {entry.id: entry.status for entry in load_inventory()}
    for rule in RULES:
        inventory_status = status_by_id.get(rule.rule_id, "unknown")
        delegates = getattr(rule, "delegates_to", None)
        suffix = f" bridge=inactive delegates_to={delegates}" if delegates else ""
        print(
            f"{rule.rule_id}\t{rule.kind.value}\t"
            f"inventory={inventory_status}\tsafe_apply={rule.safe_apply}{suffix}"
        )
    return 0


def cmd_check(paths: list[Path]) -> int:
    hits = check_paths(paths)
    print(json.dumps(hits_to_jsonable(hits), indent=2))
    return 1 if hits else 0


def cmd_fix(paths: list[Path]) -> int:
    for path in fix_paths(paths):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
