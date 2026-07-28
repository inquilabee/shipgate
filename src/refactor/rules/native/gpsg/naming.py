"""GPSG native: naming rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import HitCollector, detect_with_visitor, noop_apply
from refactor.protocol import ApplyMode, RuleKind
from refactor.rules.native.gpsg.helpers import (
    TYPE_SUFFIX_RE,
    hit_at,
    is_snake_case,
    is_upper_camel_case,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit

# Default allowlist for single-char *assignments* is empty; loop/except/with
# targets are different syntax and are not flagged. ``_`` is the discard name.
SINGLE_CHAR_ASSIGN_ALLOWLIST = frozenset({"_"})
AVOID_SINGLE_CHAR_MESSAGE = "Avoid single character names"
AVOID_SINGLE_CHAR_VARS_ID = "avoid-single-character-names-variables"
AVOID_SINGLE_CHAR_FUNCS_ID = "avoid-single-character-names-functions"


class AvoidSingleCharacterNamesVariablesRule:
    rule_id = AVOID_SINGLE_CHAR_VARS_ID
    kind = RuleKind.SUGGESTION
    summary = AVOID_SINGLE_CHAR_MESSAGE
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(
            source,
            path,
            AvoidSingleCharacterNamesVariablesRule.Finder,
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Assign(self, node: cst.Assign) -> bool:  # ruff:ignore[invalid-function-name]
            for target in node.targets:
                name = target.target
                if not isinstance(name, cst.Name):
                    continue
                if len(name.value) != 1 or name.value in SINGLE_CHAR_ASSIGN_ALLOWLIST:
                    continue
                self.record_hit(
                    hit_at(
                        rule_id=AVOID_SINGLE_CHAR_VARS_ID,
                        message=AVOID_SINGLE_CHAR_MESSAGE,
                        path=self.path,
                        node=name,
                    ),
                    name,
                )
            return True

        def visit_AnnAssign(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.AnnAssign,
        ) -> bool:
            name = node.target
            if not isinstance(name, cst.Name):
                return True
            if len(name.value) != 1 or name.value in SINGLE_CHAR_ASSIGN_ALLOWLIST:
                return True
            self.record_hit(
                hit_at(
                    rule_id=AVOID_SINGLE_CHAR_VARS_ID,
                    message=AVOID_SINGLE_CHAR_MESSAGE,
                    path=self.path,
                    node=name,
                ),
                name,
            )
            return True


class AvoidSingleCharacterNamesFunctionsRule:
    rule_id = AVOID_SINGLE_CHAR_FUNCS_ID
    kind = RuleKind.SUGGESTION
    summary = AVOID_SINGLE_CHAR_MESSAGE
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(
            source,
            path,
            AvoidSingleCharacterNamesFunctionsRule.Finder,
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.FunctionDef,
        ) -> bool:
            if len(node.name.value) != 1:
                return True
            self.record_hit(
                hit_at(
                    rule_id=AVOID_SINGLE_CHAR_FUNCS_ID,
                    message=AVOID_SINGLE_CHAR_MESSAGE,
                    path=self.path,
                    node=node.name,
                ),
                node.name,
            )
            return True


class NameTypeSuffixRule:
    rule_id = "name-type-suffix"
    kind = RuleKind.SUGGESTION
    summary = "Don't use the type of a variable as a suffix"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, NameTypeSuffixRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Assign(self, node: cst.Assign) -> bool:  # ruff:ignore[invalid-function-name]
            self.check_targets(node.targets)
            return True

        def visit_AnnAssign(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.AnnAssign,
        ) -> bool:
            if isinstance(node.target, cst.Name):
                self.maybe_hit(node.target)
            return True

        def check_targets(self, targets: Sequence[cst.AssignTarget]) -> None:
            for target in targets:
                if isinstance(target.target, cst.Name):
                    self.maybe_hit(target.target)

        def maybe_hit(self, name: cst.Name) -> None:
            if not TYPE_SUFFIX_RE.search(name.value):
                return
            self.record_hit(
                hit_at(
                    rule_id="name-type-suffix",
                    message="Don't use the type of a variable as a suffix",
                    path=self.path,
                    node=name,
                ),
                name,
            )


class SnakeCaseVariableDeclarationsRule:
    rule_id = "snake-case-variable-declarations"
    kind = RuleKind.SUGGESTION
    summary = "Use snake case for variable names"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, SnakeCaseVariableDeclarationsRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def __init__(self, *, path: str) -> None:
            super().__init__(path=path)
            self._in_function = 0

        def visit_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.FunctionDef,
        ) -> bool:
            _ = node
            self._in_function += 1
            return True

        def leave_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            original_node: cst.FunctionDef,
        ) -> None:
            _ = original_node
            self._in_function = max(0, self._in_function - 1)

        def visit_AnnAssign(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.AnnAssign,
        ) -> bool:
            # Sourcery: bare annotated locals in functions (no value) that aren't snake_case.
            if self._in_function == 0 or node.value is not None:
                return True
            if not isinstance(node.target, cst.Name) or is_snake_case(node.target.value):
                return True
            self.record_hit(
                hit_at(
                    rule_id="snake-case-variable-declarations",
                    message="Use snake case for variable names",
                    path=self.path,
                    node=node.target,
                ),
                node.target,
            )
            return True


class SnakeCaseArgumentsRule:
    rule_id = "snake-case-arguments"
    kind = RuleKind.SUGGESTION
    summary = "Use snake case for arguments"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, SnakeCaseArgumentsRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.FunctionDef,
        ) -> bool:
            for param in (
                *node.params.params,
                *node.params.posonly_params,
                *node.params.kwonly_params,
            ):
                name = param.name.value
                if name in {"self", "cls"}:
                    continue
                # Sourcery flags dunder argument names and non-snake_case names.
                dunder = name.startswith("__") and name.endswith("__")
                if not dunder and is_snake_case(name):
                    continue
                self.record_hit(
                    hit_at(
                        rule_id="snake-case-arguments",
                        message="Use snake case for arguments",
                        path=self.path,
                        node=param.name,
                    ),
                    param.name,
                )
            return True


class SnakeCaseFunctionsRule:
    rule_id = "snake-case-functions"
    kind = RuleKind.SUGGESTION
    summary = "Use snake case for function names"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, SnakeCaseFunctionsRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.FunctionDef,
        ) -> bool:
            name = node.name.value
            if name.startswith("__") and name.endswith("__"):
                return True
            if is_snake_case(name):
                return True
            self.record_hit(
                hit_at(
                    rule_id="snake-case-functions",
                    message="Use snake case for function names",
                    path=self.path,
                    node=node.name,
                ),
                node.name,
            )
            return True


class UpperCamelCaseClassesRule:
    rule_id = "upper-camel-case-classes"
    kind = RuleKind.SUGGESTION
    summary = "Use upper camel case for class names"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, UpperCamelCaseClassesRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_ClassDef(self, node: cst.ClassDef) -> bool:  # ruff:ignore[invalid-function-name]
            if is_upper_camel_case(node.name.value):
                return True
            self.record_hit(
                hit_at(
                    rule_id="upper-camel-case-classes",
                    message="Use upper camel case for class names",
                    path=self.path,
                    node=node.name,
                ),
                node.name,
            )
            return True
