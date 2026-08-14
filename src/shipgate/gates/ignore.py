"""Ignore helpers for script gates."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pathspec

from shipgate.planning.utils.gitignore import ignored_path_part, load_ignore_patterns


@dataclass(frozen=True)
class EffectiveIgnores:
    path_patterns: tuple[str, ...] = ()
    matcher: pathspec.PathSpec | None = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        compiled = (
            pathspec.PathSpec.from_lines("gitignore", self.path_patterns)
            if self.path_patterns
            else None
        )
        object.__setattr__(self, "matcher", compiled)

    def is_ignored(self, rel_path: str) -> bool:
        normalized = rel_path.replace("\\", "/")
        normalized = normalized[2:] if normalized.startswith("./") else normalized
        if ignored_path_part(normalized):
            return True
        matcher = self.matcher
        return (
            False
            if matcher is None
            else matcher.match_file(normalized)
            or (not normalized.endswith("/") and matcher.match_file(f"{normalized}/"))
        )


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
        *load_ignore_patterns(project_root),
        *extra_patterns,
    ]
    return {"SHIPGATE_IGNORE_PATHS": "\n".join(patterns)} if patterns else {}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: ignore REL_PATH", file=sys.stderr)
        return 2
    ignores = ignores_from_env()
    return (0 if ignores.is_ignored(args[0]) else 1) if ignores.path_patterns else 1


if __name__ == "__main__":
    raise SystemExit(main())
