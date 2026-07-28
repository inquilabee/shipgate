"""GPSG native: docstring rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import HitCollector, detect_with_visitor, noop_apply
from refactor.protocol import ApplyMode, RuleKind
from refactor.rules.native.gpsg.helpers import (
    class_docstring,
    function_docstring,
    hit_at,
    is_init_path,
    is_test_path,
    module_docstring,
    statement_count,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class DocstringsForClassesRule:
    rule_id = "docstrings-for-classes"
    kind = RuleKind.SUGGESTION
    summary = "Public classes should have docstrings"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return (
            []
            if is_test_path(path)
            else detect_with_visitor(source, path, DocstringsForClassesRule.Finder)
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_ClassDef(self, node: cst.ClassDef) -> bool:  # ruff:ignore[invalid-function-name]
            if node.name.value.startswith("_") or class_docstring(node) is not None:
                return True
            self.record_hit(
                hit_at(
                    rule_id="docstrings-for-classes",
                    message="Public classes should have docstrings",
                    path=self.path,
                    node=node,
                ),
                node,
            )
            return True


class DocstringsForFunctionsRule:
    rule_id = "docstrings-for-functions"
    kind = RuleKind.SUGGESTION
    summary = "Functions should have docstrings"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return (
            []
            if is_test_path(path)
            else detect_with_visitor(source, path, DocstringsForFunctionsRule.Finder)
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def __init__(self, *, path: str) -> None:
            super().__init__(path=path)
            self._function_depth = 0

        def visit_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.FunctionDef,
        ) -> bool:
            nested = self._function_depth > 0
            self._function_depth += 1
            if nested:
                return True
            name = node.name.value
            short_private = name.startswith("_") and statement_count(node.body) < 5
            if short_private or function_docstring(node) is not None:
                return True
            self.record_hit(
                hit_at(
                    rule_id="docstrings-for-functions",
                    message="Functions should have docstrings",
                    path=self.path,
                    node=node,
                ),
                node,
            )
            return True

        def leave_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            original_node: cst.FunctionDef,
        ) -> None:
            _ = original_node
            self._function_depth = max(0, self._function_depth - 1)


class DocstringsForPackagesRule:
    rule_id = "docstrings-for-packages"
    kind = RuleKind.SUGGESTION
    summary = "Packages should have docstrings"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return (
            detect_with_visitor(source, path, DocstringsForPackagesRule.Finder)
            if is_init_path(path)
            else []
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Module(self, node: cst.Module) -> bool:  # ruff:ignore[invalid-function-name]
            if module_docstring(node) is not None:
                return False
            self.record_hit(
                hit_at(
                    rule_id="docstrings-for-packages",
                    message="Packages should have docstrings",
                    path=self.path,
                    node=node,
                    before=self.path,
                ),
                node,
            )
            return False


class DocstringsForModulesRule:
    rule_id = "docstrings-for-modules"
    kind = RuleKind.SUGGESTION
    summary = "Modules should have docstrings"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return (
            []
            if is_test_path(path) or is_init_path(path)
            else detect_with_visitor(source, path, DocstringsForModulesRule.Finder)
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Module(self, node: cst.Module) -> bool:  # ruff:ignore[invalid-function-name]
            if module_docstring(node) is not None:
                return False
            self.record_hit(
                hit_at(
                    rule_id="docstrings-for-modules",
                    message="Modules should have docstrings",
                    path=self.path,
                    node=node,
                    before=self.path,
                ),
                node,
            )
            return False
