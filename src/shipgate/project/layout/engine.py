"""Classify layout roles for init-time scope scaffolding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout.collapse import PathCollapse
from shipgate.project.layout.roles import LayoutRoles
from shipgate.project.layout.scan import LayoutScanner
from shipgate.project.layout.types import DirSignals, ProjectLayout

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
        self.roles = LayoutRoles(
            configured_tests=self.configured_tests,
            marker_docs=self.marker_docs,
            signals=self.signals,
        )

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
        self.roles = LayoutRoles(
            configured_tests=self.configured_tests,
            marker_docs=self.marker_docs,
            signals=self.signals,
        )
        test_dirs, python_dirs, docs_dirs = self.classify()
        return ProjectLayout(
            python_dirs=tuple(PathCollapse.collapse_python(python_dirs, self.signals)),
            test_dirs=tuple(PathCollapse.collapse_named(test_dirs)),
            docs_dirs=tuple(self.roles.filter_docs(PathCollapse.collapse_named(docs_dirs))),
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
        if self.roles.is_docs(rel_dir, sig):
            docs_dirs.add(rel_dir)
        elif self.roles.is_test(rel_dir, sig):
            test_dirs.add(rel_dir)
        elif not self.roles.is_utility(rel_dir, sig) and self.roles.is_python(rel_dir, sig):
            python_dirs.add(rel_dir)

    @staticmethod
    def without_tests(python_dirs: set[str], test_dirs: set[str]) -> set[str]:
        return {
            path
            for path in python_dirs
            if not any(path == test or path.startswith(f"{test}/") for test in test_dirs)
        }

    def drop_empty_docs(self, docs_dirs: set[str], python_dirs: set[str]) -> None:
        for docs in list(docs_dirs):
            if docs in python_dirs and not self.signals[docs].prod_py_files:
                python_dirs.discard(docs)
