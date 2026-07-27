"""Run registered refactor rules over Python paths."""

from __future__ import annotations

from typing import TYPE_CHECKING

from refactor.registry import RULES

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from refactor.protocol import Hit, RefactorRule


def iter_python_files(paths: Sequence[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        files.extend(collect_python(path))
    return files


def collect_python(path: Path) -> list[Path]:
    resolved = path.resolve()
    if resolved.is_file() and resolved.suffix == ".py":
        return [resolved]
    if not resolved.is_dir():
        return []
    return sorted(
        candidate for candidate in resolved.rglob("*.py") if "__pycache__" not in candidate.parts
    )


def check_paths(
    paths: Sequence[Path],
    *,
    rules: Sequence[RefactorRule] | None = None,
) -> list[Hit]:
    selected = tuple(rules) if rules is not None else RULES
    hits: list[Hit] = []
    for file_path in iter_python_files(paths):
        source = file_path.read_text(encoding="utf-8")
        for rule in selected:
            hits.extend(rule.detect(source, str(file_path)))
    return hits


def fix_paths(
    paths: Sequence[Path],
    *,
    rules: Sequence[RefactorRule] | None = None,
) -> list[Path]:
    selected = tuple(rules) if rules is not None else RULES
    return [file_path for file_path in iter_python_files(paths) if fix_file(file_path, selected)]


def fix_file(file_path: Path, rules: Sequence[RefactorRule]) -> bool:
    source = file_path.read_text(encoding="utf-8")
    original = source
    for rule in rules:
        source = apply_safe_rule(rule, source, file_path)
    if source == original:
        return False
    file_path.write_text(source, encoding="utf-8")
    return True


def apply_safe_rule(rule: RefactorRule, source: str, file_path: Path) -> str:
    if not rule.safe_apply:
        return source
    hits = rule.detect(source, str(file_path))
    if not hits:
        return source
    rewritten = rule.apply(source, hits)
    if rewritten is None:
        return source
    if rule.detect(rewritten, str(file_path)):
        return source
    return rewritten


def hits_to_jsonable(hits: Sequence[Hit]) -> list[dict[str, object]]:
    return [hit_row(hit) for hit in hits]


def hit_row(hit: Hit) -> dict[str, object]:
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
    if hit.extra:
        row["extra"] = dict(hit.extra)
    return row
