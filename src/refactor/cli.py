"""Standalone CLI: check / fix / list / explain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

from refactor.config_enable import resolve_enable
from refactor.inventory import inventory_by_id, load_inventory, rule_pack_selected
from refactor.protocol import ApplyMode
from refactor.registry import RULES
from refactor.runner import (
    check_paths,
    filter_hits_by_policy,
    fix_paths,
    hits_to_jsonable,
)

if TYPE_CHECKING:
    from refactor.inventory import InventoryEntry
    from refactor.protocol import RefactorRule


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    enable = resolve_enable(getattr(args, "enable", None), project_root=Path())
    if args.command == "list":
        return cmd_list(enable=enable)
    if args.command == "explain":
        return cmd_explain(args.rule_id)
    paths: list[Path] = list(args.paths) or [Path()]
    return (
        cmd_check(paths, strict=args.strict, enable=enable)
        if args.command == "check"
        else cmd_fix(paths, enable=enable)
        if args.command == "fix"
        else 2
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="refactor")
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list", help="List registered rules")
    add_enable_argument(list_parser)
    explain_parser = sub.add_parser("explain", help="Explain a rule with catalog examples")
    explain_parser.add_argument("rule_id", help="Rule id to explain")
    check_parser = sub.add_parser("check", help="Detect issues and print JSON hits")
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Report auto + hint rules (default: auto/blocking rules only)",
    )
    add_enable_argument(check_parser)
    check_parser.add_argument("paths", nargs="*", type=Path, default=[Path()])
    fix_parser = sub.add_parser("fix", help="Apply auto (apply_mode=auto) rules")
    add_enable_argument(fix_parser)
    fix_parser.add_argument("paths", nargs="*", type=Path, default=[Path()])
    return parser.parse_args(argv)


def add_enable_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--enable",
        action="append",
        default=[],
        metavar="TAG_OR_PACK",
        help=(
            "Enable optional packs/tags (comma-separated or repeatable). "
            "Example: --enable gpsg or --enable gpsg-import,gpsg-naming"
        ),
    )


def cmd_list(*, enable: frozenset[str]) -> int:
    entries = inventory_by_id()
    status_by_id = {entry.id: entry.status for entry in entries.values()}
    for rule in RULES:
        inventory_status = status_by_id.get(rule.rule_id, "unknown")
        delegates = getattr(rule, "delegates_to", None)
        suffix = f" bridge=ruff delegates_to={delegates}" if delegates else ""
        entry = entries.get(rule.rule_id)
        pack_bits = ""
        if entry is not None and (entry.packs or entry.tags):
            selected = rule_pack_selected(rule.rule_id, enable, inventory=entries)
            packs = ",".join(entry.packs) if entry.packs else ""
            tags = ",".join(entry.tags) if entry.tags else ""
            pack_bits = f"\tpacks={packs}\ttags={tags}\tenabled={selected}"
        print(
            f"{rule.rule_id}\t{rule.kind.value}\t"
            f"inventory={inventory_status}\tapply_mode={rule.apply_mode.value}"
            f"{suffix}{pack_bits}"
        )
    return 0


def cmd_explain(rule_id: str) -> int:
    entry = next((item for item in load_inventory() if item.id == rule_id), None)
    rule = next((item for item in RULES if item.rule_id == rule_id), None)
    if entry is None and rule is None:
        print(f"unknown rule: {rule_id}")
        return 1
    print_explain_header(rule_id, rule, entry)
    print_explain_examples(rule, entry)
    return 0


def print_explain_header(
    rule_id: str,
    rule: RefactorRule | None,
    entry: InventoryEntry | None,
) -> None:
    apply_mode = (
        rule.apply_mode
        if rule is not None
        else (entry.apply_mode if entry is not None else ApplyMode.HINT)
    )
    summary = rule.summary if rule is not None else (entry.note if entry else None)
    kind = rule.kind.value if rule is not None else (entry.kind if entry else "unknown")
    print(f"rule_id: {rule_id}")
    print(f"kind: {kind}")
    print(f"apply_mode: {apply_mode.value}")
    if entry is not None and entry.packs:
        print(f"packs: {','.join(entry.packs)}")
    if entry is not None and entry.tags:
        print(f"tags: {','.join(entry.tags)}")
    if summary:
        print(f"summary: {summary}")


def print_explain_examples(
    rule: RefactorRule | None,
    entry: InventoryEntry | None,
) -> None:
    if entry is None:
        return
    summary = rule.summary if rule is not None else None
    fields = {
        "status": entry.status,
        "rationale": entry.rationale,
        "note": entry.note if entry.note != summary else None,
        "delegates_to": entry.delegates_to,
    }
    for label, value in fields.items():
        if value:
            print(f"{label}: {value}")
    examples = {
        "example_bad": entry.example_bad,
        "example_good": entry.example_good,
    }
    for label, value in examples.items():
        if value:
            print(f"{label}:")
            print(value.rstrip("\n"))


def cmd_check(
    paths: list[Path],
    *,
    strict: bool = False,
    enable: frozenset[str] | None = None,
) -> int:
    hits = filter_hits_by_policy(check_paths(paths, enable=enable), strict=strict)
    print(json.dumps(hits_to_jsonable(hits), indent=2))
    return 1 if hits else 0


def cmd_fix(paths: list[Path], *, enable: frozenset[str] | None = None) -> int:
    for path in fix_paths(paths, enable=enable):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
