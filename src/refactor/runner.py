"""Run registered refactor rules over Python paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pathspec

from refactor.detector import check_rules, detect_file
from refactor.registry import RULES

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit, RefactorRule

IGNORED_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".shipgate",
        ".tox",
        ".venv",
        "node_modules",
        "venv",
    }
)


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
    return walk_python_files(resolved, load_gitignore(resolved))


def walk_python_files(root: Path, ignore_spec: pathspec.PathSpec) -> list[Path]:
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        dirnames[:] = filter_walk_dirnames(dirnames, current_path, root, ignore_spec)
        for filename in sorted(filenames):
            candidate = current_path / filename
            if candidate.suffix != ".py":
                continue
            if should_ignore_path(candidate, root, ignore_spec, is_dir=False):
                continue
            files.append(candidate.resolve())
    return files


def filter_walk_dirnames(
    dirnames: list[str],
    current_path: Path,
    root: Path,
    ignore_spec: pathspec.PathSpec,
) -> list[str]:
    return [
        dirname
        for dirname in sorted(dirnames)
        if not should_ignore_path(current_path / dirname, root, ignore_spec, is_dir=True)
    ]


def load_gitignore(root: Path) -> pathspec.PathSpec:
    ignore_path = root / ".gitignore"
    if not ignore_path.is_file():
        return pathspec.PathSpec.from_lines("gitignore", [])
    return pathspec.PathSpec.from_lines(
        "gitignore",
        ignore_path.read_text(encoding="utf-8").splitlines(),
    )


def should_ignore_path(
    path: Path,
    root: Path,
    ignore_spec: pathspec.PathSpec,
    *,
    is_dir: bool,
) -> bool:
    if path.name in IGNORED_DIR_NAMES:
        return True
    relative = path.relative_to(root).as_posix()
    if is_dir:
        relative = f"{relative}/"
    return ignore_spec.match_file(relative)


def check_paths(
    paths: Sequence[Path],
    *,
    rules: Sequence[RefactorRule] | None = None,
) -> list[Hit]:
    selected = check_rules(rules)
    hits: list[Hit] = []
    for file_path in iter_python_files(paths):
        source = file_path.read_text(encoding="utf-8")
        hits.extend(detect_file(source, str(file_path), selected))
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
