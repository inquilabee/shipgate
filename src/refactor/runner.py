"""Run registered refactor rules over Python paths."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.detector import check_rules, detect_file
from refactor.inventory import load_inventory
from refactor.protocol import ApplyMode
from refactor.registry import RULES
from refactor.scan.gitignore import (
    load_gitignore,
    resolved_under_roots,
    walk_python_files,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from refactor.inventory import InventoryEntry
    from refactor.protocol import Hit, RefactorRule

FIX_FIXED_POINT_LIMIT = 100


def iter_python_files(paths: Sequence[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        files.extend(collect_python(path))
    return files


def collect_python(path: Path) -> list[Path]:
    resolved = path.resolve()
    return (
        [resolved]
        if resolved.is_file() and resolved.suffix == ".py"
        else (walk_python_files(resolved, load_gitignore(resolved)) if resolved.is_dir() else [])
    )


def discover_project_root(start: Path) -> Path | None:
    current = start.resolve()
    current = current.parent if current.is_file() else current
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            return candidate
    return None


FILE_SKIP_ERRORS = (
    OSError,
    UnicodeDecodeError,
    cst.ParserSyntaxError,
    cst.CSTValidationError,
)


def python_files_under_supplied_roots(paths: Sequence[Path]) -> list[Path]:
    supplied = tuple(path.resolve() for path in paths)
    return [
        file_path
        for file_path in iter_python_files(paths)
        if resolved_under_roots(file_path, supplied)
    ]


def check_paths(
    paths: Sequence[Path],
    *,
    rules: Sequence[RefactorRule] | None = None,
    enable: frozenset[str] | None = None,
) -> list[Hit]:
    selected = check_rules(rules, enable=enable)
    hits: list[Hit] = []
    for file_path in python_files_under_supplied_roots(paths):
        try:
            source = file_path.read_text(encoding="utf-8")
            hits.extend(detect_file(source, str(file_path), selected))
        except FILE_SKIP_ERRORS:
            continue
    return hits


def filter_hits_by_policy(
    hits: Sequence[Hit],
    *,
    strict: bool,
    rules: Sequence[RefactorRule] | None = None,
) -> list[Hit]:
    rules_by_id = {rule.rule_id: rule for rule in (rules if rules is not None else RULES)}
    allowed = {ApplyMode.AUTO, ApplyMode.HINT} if strict else {ApplyMode.AUTO}
    filtered: list[Hit] = []
    for hit in hits:
        rule = rules_by_id.get(hit.rule_id)
        if rule is None:
            continue
        if rule.apply_mode in allowed:
            filtered.append(hit)
    return filtered


def fix_paths(
    paths: Sequence[Path],
    *,
    rules: Sequence[RefactorRule] | None = None,
    enable: frozenset[str] | None = None,
) -> list[Path]:
    selected = check_rules(rules, enable=enable)
    auto_rules = tuple(rule for rule in selected if rule.apply_mode is ApplyMode.AUTO)
    supplied = tuple(path.resolve() for path in paths)
    project_root = discover_project_root(supplied[0]) if supplied else None
    return [
        file_path
        for file_path in python_files_under_supplied_roots(paths)
        if project_root is not None
        and resolved_under_roots(file_path, (project_root,))
        and fix_file(file_path, auto_rules)
    ]


def fix_file(file_path: Path, rules: Sequence[RefactorRule]) -> bool:
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    original = source
    try:
        for _ in range(FIX_FIXED_POINT_LIMIT):
            updated = source
            for rule in rules:
                updated = apply_auto_rule(rule, updated, file_path)
            if updated == source:
                break
            source = updated
    except FILE_SKIP_ERRORS:
        return False
    if source == original:
        return False
    file_path.write_text(source, encoding="utf-8")
    return True


def apply_auto_rule(rule: RefactorRule, source: str, file_path: Path) -> str:
    if rule.apply_mode is not ApplyMode.AUTO:
        return source
    hits = rule.detect(source, str(file_path))
    if not hits:
        return source
    rewritten = rule.apply(source, hits)
    return (
        source
        if rewritten is None
        else source
        if rule.detect(rewritten, str(file_path))
        else rewritten
    )


def hits_to_jsonable(
    hits: Sequence[Hit],
    *,
    inventory: Sequence[InventoryEntry] | None = None,
) -> list[dict[str, object]]:
    entries = (
        {entry.id: entry for entry in inventory}
        if inventory is not None
        else {entry.id: entry for entry in load_inventory()}
    )
    return [hit_row(hit, inventory_by_id=entries) for hit in hits]


def hit_row(
    hit: Hit,
    *,
    inventory_by_id: dict[str, InventoryEntry] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "rule_id": hit.rule_id,
        "message": hit.message,
        "location": {
            "path": hit.location.path,
            "line": hit.location.line,
            "column": hit.location.column,
        },
    }
    if hit.suggestion is not None:
        row["suggestion"] = {
            "before": hit.suggestion.before,
            "after": hit.suggestion.after,
            "message": hit.suggestion.message,
        }
    elif inventory_by_id is not None:
        entry = inventory_by_id.get(hit.rule_id)
        if entry is not None and (entry.example_bad or entry.example_good):
            suggestion: dict[str, object] = {}
            if entry.example_bad is not None:
                suggestion["before"] = entry.example_bad
            if entry.example_good is not None:
                suggestion["after"] = entry.example_good
            if entry.rationale is not None:
                suggestion["message"] = entry.rationale
            row["suggestion"] = suggestion
    if hit.extra:
        row["extra"] = dict(hit.extra)
    return row
