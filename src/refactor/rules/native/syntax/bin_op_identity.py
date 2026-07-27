"""Simplify ``x + 0`` and ``x * 1`` to ``x`` for simple names."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    apply_with_transformer,
    code_for_small_stmt,
    detect_with_visitor,
    make_hit,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class BinOpIdentityRule:
    rule_id = "bin-op-identity"
    kind = RuleKind.REFACTOR
    summary = "Replace `x + 0` and `x * 1` with `x` for simple names"
    safe_apply = True

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, BinOpIdentityRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, BinOpIdentityRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_Assign(  # ruff:ignore[invalid-function-name]
            self,
            original_node: cst.Assign,
            updated_node: cst.Assign,
        ) -> cst.Assign:
            _ = self, original_node
            identity = BinOpIdentityRule.match_identity_assign(updated_node)
            if identity is None:
                return updated_node
            return updated_node.with_changes(value=identity)

    class Finder(HitCollector):
        def visit_Assign(self, node: cst.Assign) -> bool:  # ruff:ignore[invalid-function-name]
            identity = BinOpIdentityRule.match_identity_assign(node)
            if identity is None:
                return True
            self.hits.append(BinOpIdentityRule.hit_for(node, identity, self.path))
            return True

    @staticmethod
    def match_identity_assign(node: cst.Assign) -> cst.Name | None:
        if len(node.targets) != 1:
            return None
        return BinOpIdentityRule.match_identity(node.value)

    @staticmethod
    def match_identity(node: cst.BaseExpression) -> cst.Name | None:
        if not isinstance(node, cst.BinaryOperation):
            return None
        return BinOpIdentityRule.identity_name(node.operator, node.left, node.right)

    @staticmethod
    def identity_name(
        operator: cst.BaseBinaryOp,
        left: cst.BaseExpression,
        right: cst.BaseExpression,
    ) -> cst.Name | None:
        if not isinstance(left, cst.Name) or not isinstance(right, cst.Integer):
            return None
        if isinstance(operator, cst.Add) and right.value == "0":
            return left
        if isinstance(operator, cst.Multiply) and right.value == "1":
            return left
        return None

    @staticmethod
    def hit_for(node: cst.Assign, identity: cst.Name, path: str) -> Hit:
        after_assign = cst.Assign(targets=node.targets, value=identity)
        return make_hit(
            rule_id="bin-op-identity",
            message="Remove identity binary operation",
            path=path,
            before=code_for_small_stmt(node),
            after=code_for_small_stmt(after_assign),
        )
