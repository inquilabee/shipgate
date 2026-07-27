"""Native rule for ``remove-redundant-constructor-in-dict-union``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BinaryOpRewriteRule


class RemoveRedundantConstructorInDictUnionRule(BinaryOpRewriteRule):
    rule_id = "remove-redundant-constructor-in-dict-union"
    summary = "Remove redundant constructor in dict union"
    message = "Remove redundant dict() around dictionary union operands"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.BinaryOperation) or not isinstance(node.operator, cst.BitOr):
            return None
        left = cls.unwrap_dict_call(node.left)
        right = cls.unwrap_dict_call(node.right)
        if left is None and right is None:
            return None
        return node.with_changes(left=left or node.left, right=right or node.right)

    @staticmethod
    def unwrap_dict_call(node: cst.BaseExpression) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "dict":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        return node.args[0].value
