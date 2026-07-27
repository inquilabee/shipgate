"""Directory role predicates for layout scope detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout.types import (
    DOC_BASENAMES,
    TEST_DIR_BASENAMES,
    UTILITY_PY_BASENAMES,
    DirSignals,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class LayoutRoles:
    """Classify a relative directory as utility, test, docs, or python."""

    def __init__(
        self,
        *,
        configured_tests: set[str],
        marker_docs: set[str],
        signals: Mapping[str, DirSignals],
    ) -> None:
        self.configured_tests = configured_tests
        self.marker_docs = marker_docs
        self.signals = signals

    @staticmethod
    def basename(rel_dir: str) -> str:
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

    def filter_docs(self, docs: list[str]) -> list[str]:
        return [
            path
            for path in docs
            if self.basename(path) in DOC_BASENAMES or path in self.marker_docs
        ]
