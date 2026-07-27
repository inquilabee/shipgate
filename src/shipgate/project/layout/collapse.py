"""Collapse directory candidate sets for layout scopes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout.types import DirSignals

if TYPE_CHECKING:
    from collections.abc import Mapping


class PathCollapse:
    """Ancestor folding helpers for python/test/docs directory sets."""

    @staticmethod
    def fold_src(candidates: set[str]) -> set[str]:
        under_src = {c for c in candidates if c == "src" or c.startswith("src/")}
        if not under_src:
            return candidates
        return (candidates - under_src) | {"src"}

    @staticmethod
    def collapse_ancestors(candidates: set[str]) -> list[str]:
        ordered = sorted(candidates, key=lambda s: (s.count("/"), s))
        kept: list[str] = []
        for rel in ordered:
            if any(rel == path or rel.startswith(f"{path}/") for path in kept):
                continue
            kept.append(rel)
        return kept

    @classmethod
    def collapse_named(cls, candidates: set[str]) -> list[str]:
        return sorted(cls.collapse_ancestors(candidates))

    @classmethod
    def collapse_python(
        cls,
        candidates: set[str],
        signals: Mapping[str, DirSignals],
    ) -> list[str]:
        if not candidates:
            return []
        folded = cls.fold_src(candidates)
        kept = cls.collapse_ancestors(folded)
        return cls.drop_empty_root(kept, signals)

    @staticmethod
    def drop_empty_root(
        kept: list[str],
        signals: Mapping[str, DirSignals],
    ) -> list[str]:
        empty = signals.get("", DirSignals())
        if "" in kept and (len(kept) > 1 or not empty.prod_py_files):
            kept = [path for path in kept if path]
        return sorted(kept)
