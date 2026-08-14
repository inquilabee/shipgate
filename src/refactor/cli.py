"""Refactor CLI (invoked as ``shipgate refactor`` or ``python -m refactor``)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

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
    from collections.abc import Sequence

    from refactor.inventory import InventoryEntry
    from refactor.protocol import RefactorRule

DOGFOOD_PATHS = (Path("src"), Path("tests/refactor"))
DEFAULT_PROG = "python -m refactor"
PATHS_HELP = (
    "Python files or directories (default: src and tests/refactor when present; "
    "'.' maps to that dogfood scope). Pass tests/unit explicitly to scan fixture trees."
)

app = typer.Typer(add_completion=False, no_args_is_help=True)


def main(argv: list[str] | None = None, *, prog: str = DEFAULT_PROG) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    try:
        result = app(args=args, prog_name=prog, standalone_mode=False)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 1
    except typer.Exit as exc:
        return exc.exit_code if isinstance(exc.exit_code, int) else 1
    return result if isinstance(result, int) else 0


def resolve_cli_paths(
    paths: Sequence[Path],
    *,
    cwd: Path | None = None,
    prog: str = DEFAULT_PROG,
) -> list[Path]:
    """Prefer dogfood roots for empty args or project-root ``.``."""
    root = cwd if cwd is not None else Path.cwd()
    dogfood = [root / path for path in DOGFOOD_PATHS if (root / path).exists()]
    requested = list(paths)
    if not requested or is_project_root_only(requested, root=root):
        if dogfood:
            if requested:
                print(
                    f"{prog}: '.' uses dogfood scope "
                    f"{' '.join(str(path.relative_to(root)) for path in dogfood)} "
                    "(pass tests/unit explicitly to include fixture trees)",
                    file=sys.stderr,
                )
            return dogfood
        return [root]
    return requested


def is_project_root_only(paths: Sequence[Path], *, root: Path) -> bool:
    if len(paths) != 1:
        return False
    candidate = paths[0]
    return candidate == Path() or candidate.resolve() == root.resolve()


EnableOpt = Annotated[
    list[str] | None,
    typer.Option(
        "--enable",
        help=(
            "Enable optional packs/tags (comma-separated or repeatable). "
            "Example: --enable gpsg or --enable gpsg-import,gpsg-naming"
        ),
    ),
]


def enable_set(raw: list[str] | None) -> frozenset[str]:
    return resolve_enable(raw or [], project_root=Path())


@app.command("list")
def list_cmd(enable: EnableOpt = None) -> None:
    raise typer.Exit(cmd_list(enable=enable_set(enable)))


@app.command("explain")
def explain_cmd(rule_id: Annotated[str, typer.Argument()]) -> None:
    raise typer.Exit(cmd_explain(rule_id))


@app.command("check")
def check_cmd(
    paths: Annotated[list[Path] | None, typer.Argument(help=PATHS_HELP)] = None,
    *,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Report auto + hint rules"),
    ] = False,
    enable: EnableOpt = None,
) -> None:
    resolved = resolve_cli_paths(list(paths or []), prog=app.info.name or DEFAULT_PROG)
    raise typer.Exit(
        cmd_check(resolved, strict=strict, enable=enable_set(enable)),
    )


@app.command("fix")
def fix_cmd(
    paths: Annotated[list[Path] | None, typer.Argument(help=PATHS_HELP)] = None,
    *,
    enable: EnableOpt = None,
) -> None:
    resolved = resolve_cli_paths(list(paths or []), prog=app.info.name or DEFAULT_PROG)
    raise typer.Exit(cmd_fix(resolved, enable=enable_set(enable)))


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


def explain_apply_mode(
    rule: RefactorRule | None,
    entry: InventoryEntry | None,
) -> ApplyMode:
    return (
        rule.apply_mode
        if rule is not None
        else entry.apply_mode
        if entry is not None
        else ApplyMode.HINT
    )


def explain_kind(rule: RefactorRule | None, entry: InventoryEntry | None) -> str:
    return rule.kind.value if rule is not None else (entry.kind if entry is not None else "unknown")


def explain_summary(rule: RefactorRule | None, entry: InventoryEntry | None) -> str | None:
    return rule.summary if rule is not None else (entry.note if entry is not None else None)


def print_explain_header(
    rule_id: str,
    rule: RefactorRule | None,
    entry: InventoryEntry | None,
) -> None:
    apply_mode = explain_apply_mode(rule, entry)
    summary = explain_summary(rule, entry)
    kind = explain_kind(rule, entry)
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
