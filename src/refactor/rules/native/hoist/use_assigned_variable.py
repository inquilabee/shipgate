"""Native rule for ``use-assigned-variable`` (Sourcery parity)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    code_for_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import RuleKind
from refactor.rules.native.stmt_base import ReturnAssignedExpressionRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class UseAssignedVariableRule:
    """Reuse a previously assigned local instead of repeating its expression."""

    rule_id = "use-assigned-variable"
    kind = RuleKind.REFACTOR
    summary = "Use previously assigned local variable"
    message = "Reuse the assigned local instead of repeating its expression"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, UseAssignedVariableRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_IndentedBlock(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.IndentedBlock,
        ) -> bool:
            UseAssignedVariableRule.check_body(node.body, self)
            return True

    @staticmethod
    def check_body(body: Sequence[cst.BaseStatement], collector: HitCollector) -> None:
        for index, stmt in enumerate(body):
            assignment = ReturnAssignedExpressionRule.name_assign_stmt(stmt)
            if assignment is None:
                continue
            name, value = assignment
            if UseAssignedVariableRule._skip_assignment(name, value):
                continue
            for later in body[index + 1 :]:
                if UseAssignedVariableRule._reassigns_name(later, name):
                    break
                replacement = UseAssignedVariableRule._replace_expr(later, value, name)
                if replacement is None:
                    continue
                collector.record_hit(
                    make_hit(
                        rule_id=UseAssignedVariableRule.rule_id,
                        message=UseAssignedVariableRule.message,
                        path=collector.path,
                        before=code_for_stmt(later),
                        after=code_for_stmt(replacement),
                    ),
                    later,
                )
                break

    @staticmethod
    def _skip_assignment(name: str, value: cst.BaseExpression) -> bool:
        # Skip trivial aliases, literals, non-self name aliases, and impure calls.
        return (
            UseAssignedVariableRule._trivial_alias(name, value)
            or UseAssignedVariableRule._constant_literal(value)
            or (isinstance(value, cst.Name) and value.value != "self")
            or UseAssignedVariableRule._contains_call(value)
        )

    @staticmethod
    def _trivial_alias(name: str, value: cst.BaseExpression) -> bool:
        return isinstance(value, cst.Name) and value.value == name

    @staticmethod
    def _constant_literal(value: cst.BaseExpression) -> bool:
        return (
            True
            if isinstance(
                value,
                (
                    cst.Integer,
                    cst.Float,
                    cst.Imaginary,
                    cst.SimpleString,
                    cst.ConcatenatedString,
                    cst.Ellipsis,
                ),
            )
            else isinstance(value, cst.Name) and value.value in {"None", "True", "False"}
        )

    @staticmethod
    def _contains_call(value: cst.BaseExpression) -> bool:
        class CallFinder(cst.CSTVisitor):
            def __init__(self) -> None:
                self.found = False

            def visit_Call(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.Call,
            ) -> bool:
                _ = node
                self.found = True
                return False

        finder = CallFinder()
        value.visit(finder)
        return finder.found

    @staticmethod
    def _reassigns_name(stmt: cst.BaseStatement, name: str) -> bool:
        assignment = ReturnAssignedExpressionRule.name_assign_stmt(stmt)
        return assignment is not None and assignment[0] == name

    @staticmethod
    def _replace_expr(
        stmt: cst.BaseStatement,
        value: cst.BaseExpression,
        name: str,
    ) -> cst.BaseStatement | None:
        transformer = UseAssignedVariableRule.ReplaceExpression(value=value, name=name)
        updated = stmt.visit(transformer)
        return (
            None
            if not transformer.replaced or not isinstance(updated, cst.BaseStatement)
            else updated
        )

    class ReplaceExpression(cst.CSTTransformer):
        """Replace deep-equal copies of ``value`` with a Name reference."""

        def __init__(self, *, value: cst.BaseExpression, name: str) -> None:
            self.value = value
            self.name = name
            self.replaced = False

        def visit_AssignTarget(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.AssignTarget,
        ) -> bool:
            """Do not rewrite assignment targets (reads only)."""
            _ = self, node
            return False

        def visit_AugAssign(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.AugAssign,
        ) -> bool:
            # Visit RHS only; do not rewrite the augmented target.
            node.value.visit(self)
            return False

        def visit_AnnAssign(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.AnnAssign,
        ) -> bool:
            if node.value is not None:
                node.value.visit(self)
            return False

        def on_leave(
            self,
            original_node: cst.CSTNode,
            updated_node: cst.CSTNode,
        ) -> cst.CSTNode:
            if not isinstance(original_node, cst.BaseExpression):
                return updated_node
            if not original_node.deep_equals(self.value):
                return updated_node
            self.replaced = True
            return cst.Name(self.name)
