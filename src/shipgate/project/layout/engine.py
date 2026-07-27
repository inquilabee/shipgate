"""Classify layout roles for init-time scope scaffolding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout.scan import LayoutScanner
from shipgate.project.layout.types import (
    DOC_BASENAMES,
    TEST_DIR_BASENAMES,
    UTILITY_PY_BASENAMES,
    DirSignals,
    ProjectLayout,
)

if TYPE_CHECKING:
    from pathlib import Path


class LayoutEngine:
    """Detect directory roles under one project root."""

    def __init__(self, project_root: Path) -> None:
        self.root = project_root.resolve()
        self.scanner = LayoutScanner(self.root)
        self.signals: dict[str, DirSignals] = {}
        self.configured_tests: set[str] = set()
        self.marker_docs: set[str] = set()
        self.notes: list[str] = []

    def detect(self) -> ProjectLayout:
        testpaths, python_files = self.scanner.parse_pytest()
        self.notes = []
        if testpaths:
            self.notes.append(f"pytest testpaths={testpaths}")
        if python_files:
            self.notes.append(f"pytest python_files={python_files}")
        self.marker_docs = set(self.scanner.docs_markers())
        if self.marker_docs:
            self.notes.append(f"docs markers={sorted(self.marker_docs)}")
        self.configured_tests = {tp.strip("/").replace("\\", "/") for tp in testpaths}
        self.signals = self.scanner.walk()
        test_dirs, python_dirs, docs_dirs = self.classify()
        return ProjectLayout(
            python_dirs=tuple(self.collapse_python(python_dirs)),
            test_dirs=tuple(self.collapse_named(test_dirs)),
            docs_dirs=tuple(self.filter_docs(self.collapse_named(docs_dirs))),
            notes=tuple(self.notes),
        )

    def classify(self) -> tuple[set[str], set[str], set[str]]:
        test_dirs = {p for p in self.configured_tests if (self.root / p).is_dir()}
        docs_dirs = {p for p in self.marker_docs if (self.root / p).is_dir()}
        python_dirs: set[str] = set()
        for rel_dir, sig in self.signals.items():
            self.assign_role(rel_dir, sig, test_dirs, python_dirs, docs_dirs)
        python_dirs = self.without_tests(python_dirs, test_dirs)
        self.drop_empty_docs(docs_dirs, python_dirs)
        return test_dirs, python_dirs, docs_dirs

    def assign_role(
        self,
        rel_dir: str,
        sig: DirSignals,
        test_dirs: set[str],
        python_dirs: set[str],
        docs_dirs: set[str],
    ) -> None:
        if self.is_docs(rel_dir, sig):
            docs_dirs.add(rel_dir)
        elif self.is_test(rel_dir, sig):
            test_dirs.add(rel_dir)
        elif not self.is_utility(rel_dir, sig) and self.is_python(rel_dir, sig):
            python_dirs.add(rel_dir)

    def without_tests(self, python_dirs: set[str], test_dirs: set[str]) -> set[str]:
        _ = self
        return {
            path
            for path in python_dirs
            if not any(path == test or path.startswith(f"{test}/") for test in test_dirs)
        }

    def drop_empty_docs(self, docs_dirs: set[str], python_dirs: set[str]) -> None:
        for docs in list(docs_dirs):
            if docs in python_dirs and not self.signals[docs].prod_py_files:
                python_dirs.discard(docs)

    def basename(self, rel_dir: str) -> str:
        _ = self
        return rel_dir.rsplit("/", 1)[-1].lower() if rel_dir else ""

    def is_utility(self, rel_dir: str, sig: DirSignals) -> bool:
        if not rel_dir:
            return False
        if not any(self.basename(part) in UTILITY_PY_BASENAMES for part in rel_dir.split("/")):
            return False
        return not ("/" not in rel_dir and sig.has_init)

    def is_test(self, rel_dir: str, sig: DirSignals) -> bool:
        if self.test_configured(rel_dir):
            return True
        return self.test_heuristic(rel_dir, sig)

    def test_configured(self, rel_dir: str) -> bool:
        if rel_dir in self.configured_tests:
            return True
        base = self.basename(rel_dir)
        under = any(rel_dir.startswith(f"{tp}/") for tp in self.configured_tests)
        return under and base in TEST_DIR_BASENAMES

    def test_heuristic(self, rel_dir: str, sig: DirSignals) -> bool:
        base = self.basename(rel_dir)
        if base in TEST_DIR_BASENAMES:
            return bool(sig.py_files) or sig.has_conftest
        if sig.has_conftest and not sig.prod_py_files and sig.test_py_files:
            return True
        if not sig.py_files:
            return False
        return len(sig.test_py_files) / len(sig.py_files) >= 0.5 and not sig.prod_py_files

    def is_docs(self, rel_dir: str, sig: DirSignals) -> bool:
        if not rel_dir:
            return False
        base = self.basename(rel_dir)
        if rel_dir in self.marker_docs or base in DOC_BASENAMES:
            return True
        if not sig.doc_files:
            return False
        named = base in DOC_BASENAMES or "doc" in base
        return named and len(sig.doc_files) >= 3 and len(sig.doc_files) > len(sig.py_files)

    def is_python(self, rel_dir: str, sig: DirSignals) -> bool:
        if sig.prod_py_files:
            return True
        if sig.has_init and sig.py_files and not sig.test_py_files:
            return True
        if rel_dir != "src":
            return False
        return any(
            child.has_init or child.prod_py_files
            for path, child in self.signals.items()
            if path.startswith("src/")
        )

    def collapse_python(self, candidates: set[str]) -> list[str]:
        if not candidates:
            return []
        folded = self.fold_src(candidates)
        kept = self.collapse_ancestors(folded)
        return self.drop_empty_root(kept)

    def fold_src(self, candidates: set[str]) -> set[str]:
        _ = self
        under_src = {c for c in candidates if c == "src" or c.startswith("src/")}
        if not under_src:
            return candidates
        return (candidates - under_src) | {"src"}

    def drop_empty_root(self, kept: list[str]) -> list[str]:
        empty = self.signals.get("", DirSignals())
        if "" in kept and (len(kept) > 1 or not empty.prod_py_files):
            kept = [path for path in kept if path]
        return sorted(kept)

    def collapse_named(self, candidates: set[str]) -> list[str]:
        return sorted(self.collapse_ancestors(candidates))

    def collapse_ancestors(self, candidates: set[str]) -> list[str]:
        _ = self
        ordered = sorted(candidates, key=lambda s: (s.count("/"), s))
        kept: list[str] = []
        for rel in ordered:
            if any(rel == path or rel.startswith(f"{path}/") for path in kept):
                continue
            kept.append(rel)
        return kept

    def filter_docs(self, docs: list[str]) -> list[str]:
        return [
            path
            for path in docs
            if self.basename(path) in DOC_BASENAMES or path in self.marker_docs
        ]
