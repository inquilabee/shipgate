"""Replace ``len(x) == 0`` with ``not x`` for names and attributes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class UseLenRule:
    rule_id = "use-len"
    kind = RuleKind.REFACTOR
    summary = "Replace `len(x) == 0` with `not x`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = UseLenRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_Comparison(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.Comparison,
        ) -> bool:
            subject = UseLenRule.len_zero_subject(node)
            if subject is None:
                return True
            self.hits.append(UseLenRule.hit_for(node, subject, self.path))
            return True

    @staticmethod
    def len_zero_subject(node: cst.Comparison) -> cst.BaseExpression | None:
        if len(node.comparisons) != 1:
            return None
        comparison = node.comparisons[0]
        if not isinstance(comparison.operator, cst.Equal):
            return None
        if not UseLenRule.is_zero(comparison.comparator):
            return None
        if not isinstance(node.left, cst.Call):
            return None
        if not UseLenRule.is_len_call(node.left):
            return None
        if not node.left.args:
            return None
        subject = node.left.args[0].value
        if not isinstance(subject, (cst.Name, cst.Attribute)):
            return None
        return subject

    @staticmethod
    def is_len_call(node: cst.Call) -> bool:
        return isinstance(node.func, cst.Name) and node.func.value == "len"

    @staticmethod
    def is_zero(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Integer) and node.value == "0"

    @staticmethod
    def hit_for(
        node: cst.Comparison,
        subject: cst.BaseExpression,
        path: str,
    ) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=node)])]
        ).code.strip()
        after_expr = cst.UnaryOperation(operator=cst.Not(), expression=subject)
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=after_expr)])]
        ).code.strip()
        return Hit(
            rule_id="use-len",
            message="Prefer truthiness over `len(x) == 0`",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
