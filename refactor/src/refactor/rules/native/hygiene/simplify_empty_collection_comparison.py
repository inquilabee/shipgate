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
        if isinstance(target.operator, cst.Equal):
            return cls.replacement_for_equal(node.left, target.comparator)
        if isinstance(target.operator, cst.NotEqual):
            return cls.replacement_for_not_equal(node.left, target.comparator)
        return None

    @classmethod
    def replacement_for_equal(
        cls,
        left: cst.BaseExpression,
        right: cst.BaseExpression,
    ) -> cst.BaseExpression | None:
        if cls.is_empty_collection(right) and not cls.is_empty_collection(left):
            return cst.UnaryOperation(operator=cst.Not(), expression=left)
        if cls.is_empty_collection(left) and not cls.is_empty_collection(right):
            return cst.UnaryOperation(operator=cst.Not(), expression=right)
        return None

    @classmethod
    def replacement_for_not_equal(
        cls,
        left: cst.BaseExpression,
        right: cst.BaseExpression,
    ) -> cst.BaseExpression | None:
        if cls.is_empty_collection(right) and not cls.is_empty_collection(left):
            return left
        if cls.is_empty_collection(left) and not cls.is_empty_collection(right):
            return right
        return None

    @staticmethod
    def is_empty_collection(node: cst.BaseExpression) -> bool:
        if isinstance(node, cst.List | cst.Tuple | cst.Set):
            return not node.elements
        return isinstance(node, cst.Dict) and not node.elements
