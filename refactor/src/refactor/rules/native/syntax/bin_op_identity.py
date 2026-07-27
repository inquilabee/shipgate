"""Simplify ``x + 0`` and ``x * 1`` to ``x`` for simple names."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class BinOpIdentityRule:
    rule_id = "bin-op-identity"
    kind = RuleKind.REFACTOR
    summary = "Replace `x + 0` and `x * 1` with `x` for simple names"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = BinOpIdentityRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_Assign(self, node: cst.Assign) -> bool:  # ruff:ignore[invalid-function-name]
            if len(node.targets) != 1:
                return True
            identity = BinOpIdentityRule.match_identity(node.value)
            if identity is None:
                return True
            self.hits.append(BinOpIdentityRule.hit_for(node, identity, self.path))
            return True

    @staticmethod
    def match_identity(node: cst.BaseExpression) -> cst.Name | None:
        if not isinstance(node, cst.BinaryOperation):
            return None
        if not isinstance(node.left, cst.Name):
            return None
        if not isinstance(node.right, cst.Integer):
            return None
        if isinstance(node.operator, cst.Add) and node.right.value == "0":
            return node.left
        if isinstance(node.operator, cst.Multiply) and node.right.value == "1":
            return node.left
        return None

    @staticmethod
    def hit_for(node: cst.Assign, identity: cst.Name, path: str) -> Hit:
        before = cst.Module(body=[cst.SimpleStatementLine(body=[node])]).code.strip()
        after_assign = cst.Assign(targets=node.targets, value=identity)
        after = cst.Module(body=[cst.SimpleStatementLine(body=[after_assign])]).code.strip()
        return Hit(
            rule_id="bin-op-identity",
            message="Remove identity binary operation",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
