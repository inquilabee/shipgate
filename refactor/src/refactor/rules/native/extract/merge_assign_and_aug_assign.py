"""Native rule for ``merge-assign-and-aug-assign``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import SimpleStatementLineRewriteRule


class MergeAssignAndAugAssignRule(SimpleStatementLineRewriteRule):
    rule_id = "merge-assign-and-aug-assign"
    summary = "Merge assign and aug assign"
    message = "Use augmented assignment for self-updates"

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        if not isinstance(node, cst.Assign) or len(node.targets) != 1:
            return None
        target = node.targets[0].target
        if not isinstance(node.value, cst.BinaryOperation):
            return None
        if not target.deep_equals(node.value.left):
            return None
        operator = cls.aug_operator(node.value.operator)
        if operator is None:
            return None
        return cst.AugAssign(target=target, operator=operator, value=node.value.right)

    @staticmethod
    def aug_operator(operator: cst.BaseBinaryOp) -> cst.BaseAugOp | None:
        mapping: dict[type[cst.BaseBinaryOp], cst.BaseAugOp] = {
            cst.Add: cst.AddAssign(),
            cst.Subtract: cst.SubtractAssign(),
            cst.Multiply: cst.MultiplyAssign(),
            cst.Divide: cst.DivideAssign(),
            cst.Modulo: cst.ModuloAssign(),
        }
        return mapping.get(type(operator))
