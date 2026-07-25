"""Ignore helpers for script gates."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pathspec

from shipgate.planning.utils.gitignore import default_ignores, load_gitignore_lines


@dataclass(frozen=True)
class EffectiveIgnores:
    path_patterns: tuple[str, ...] = ()

    def is_ignored(self, rel_path: str) -> bool:
        normalized = rel_path.replace("\\", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        if not self.path_patterns:
            return False
        matcher = pathspec.PathSpec.from_lines("gitignore", self.path_patterns)
        return matcher.match_file(normalized)


def patterns_from_env() -> tuple[str, ...]:
    patterns = [
        pattern.strip()
        for pattern in os.environ.get("SHIPGATE_IGNORE_PATHS", "").splitlines()
        if pattern.strip()
    ]
    for profile in os.environ.get("SHIPGATE_IGNORE_PROFILES", "").splitlines():
        path = Path(profile.strip())
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("!"):
                patterns.append(stripped)
    return tuple(patterns)


def ignores_from_env(_project_root: Path | None = None) -> EffectiveIgnores:
    return EffectiveIgnores(path_patterns=patterns_from_env())


def ignore_env(project_root: Path, extra_patterns: tuple[str, ...] = ()) -> dict[str, str]:
    patterns = [
        *default_ignores(),
        *load_gitignore_lines(project_root),
        *extra_patterns,
    ]
    if not patterns:
        return {}
    return {"SHIPGATE_IGNORE_PATHS": "\n".join(patterns)}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: ignore REL_PATH", file=sys.stderr)
        return 2
    ignores = ignores_from_env()
    if not ignores.path_patterns:
        return 1
    if ignores.is_ignored(args[0]):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
