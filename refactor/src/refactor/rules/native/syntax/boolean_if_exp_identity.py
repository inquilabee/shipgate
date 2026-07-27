"""Simplify boolean ``if`` expressions like ``True if cond else False``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class BooleanIfExpIdentityRule:
    rule_id = "boolean-if-exp-identity"
    kind = RuleKind.REFACTOR
    summary = "Simplify `True if cond else False` to `cond`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = BooleanIfExpIdentityRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_IfExp(self, node: cst.IfExp) -> bool:  # ruff:ignore[invalid-function-name]
            replacement = BooleanIfExpIdentityRule.match_identity(node)
            if replacement is None:
                return True
            self.hits.append(BooleanIfExpIdentityRule.hit_for(node, replacement, self.path))
            return True

    @staticmethod
    def is_true(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Name) and node.value == "True"

    @staticmethod
    def is_false(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Name) and node.value == "False"

    @staticmethod
    def match_identity(node: cst.IfExp) -> cst.BaseExpression | None:
        if BooleanIfExpIdentityRule.is_true(node.body) and BooleanIfExpIdentityRule.is_false(
            node.orelse
        ):
            return node.test
        if BooleanIfExpIdentityRule.is_false(node.body) and BooleanIfExpIdentityRule.is_true(
            node.orelse
        ):
            return cst.UnaryOperation(operator=cst.Not(), expression=node.test)
        return None

    @staticmethod
    def hit_for(
        node: cst.IfExp,
        replacement: cst.BaseExpression,
        path: str,
    ) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=node)])]
        ).code.strip()
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=replacement)])]
        ).code.strip()
        return Hit(
            rule_id="boolean-if-exp-identity",
            message="Simplify boolean if-expression",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
