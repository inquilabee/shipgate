"""Native rule for ``simplify-empty-collection-comparison``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import ComparisonRewriteRule


class SimplifyEmptyCollectionComparisonRule(ComparisonRewriteRule):
    rule_id = "simplify-empty-collection-comparison"
    summary = "Simplify empty collection comparison"
    message = "Use collection truthiness instead of comparing to an empty literal"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        target = node.comparisons[0]
        return (
            cls.replacement_for_equal(node.left, target.comparator)
            if isinstance(target.operator, cst.Equal)
            else (
                cls.replacement_for_not_equal(node.left, target.comparator)
                if isinstance(target.operator, cst.NotEqual)
                else None
            )
        )

    @classmethod
    def replacement_for_equal(
        cls,
        left: cst.BaseExpression,
        right: cst.BaseExpression,
    ) -> cst.BaseExpression | None:
        return (
            cst.UnaryOperation(operator=cst.Not(), expression=left)
            if cls.is_empty_collection(right) and not cls.is_empty_collection(left)
            else (
                cst.UnaryOperation(operator=cst.Not(), expression=right)
                if cls.is_empty_collection(left) and not cls.is_empty_collection(right)
                else None
            )
        )

    @classmethod
    def replacement_for_not_equal(
        cls,
        left: cst.BaseExpression,
        right: cst.BaseExpression,
    ) -> cst.BaseExpression | None:
        return (
            left
            if cls.is_empty_collection(right) and not cls.is_empty_collection(left)
            else (
                right
                if cls.is_empty_collection(left) and not cls.is_empty_collection(right)
                else None
            )
        )

    @staticmethod
    def is_empty_collection(node: cst.BaseExpression) -> bool:
        return (
            not node.elements
            if isinstance(node, cst.List | cst.Tuple | cst.Set)
            else isinstance(node, cst.Dict) and not node.elements
        )
