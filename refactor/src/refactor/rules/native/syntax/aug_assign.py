"""Replace ``x = x + y`` with augmented assignment when safe."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    code_for_small_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class AugAssignRule:
    rule_id = "aug-assign"
    kind = RuleKind.REFACTOR
    summary = "Replace `x = x + y` with `x += y` for simple names"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, AugAssignRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Assign(self, node: cst.Assign) -> bool:  # ruff:ignore[invalid-function-name]
            aug = AugAssignRule.match_aug_assign(node)
            if aug is None:
                return True
            self.hits.append(AugAssignRule.hit_for(node, aug, self.path))
            return True

    @staticmethod
    def match_aug_assign(node: cst.Assign) -> cst.AugAssign | None:
        if len(node.targets) != 1:
            return None
        target = node.targets[0].target
        if not isinstance(target, cst.Name):
            return None
        if not isinstance(node.value, cst.BinaryOperation):
            return None
        if not isinstance(node.value.left, cst.Name):
            return None
        if node.value.left.value != target.value:
            return None
        aug_op = AugAssignRule.binop_to_aug(node.value.operator)
        if aug_op is None:
            return None
        return cst.AugAssign(target=target, operator=aug_op, value=node.value.right)

    @staticmethod
    def binop_to_aug(
        operator: cst.BaseBinaryOp,
    ) -> cst.BaseAugOp | None:
        if isinstance(operator, cst.Add):
            return cst.AddAssign()
        if isinstance(operator, cst.Subtract):
            return cst.SubtractAssign()
        if isinstance(operator, cst.Multiply):
            return cst.MultiplyAssign()
        return None

    @staticmethod
    def hit_for(node: cst.Assign, aug: cst.AugAssign, path: str) -> Hit:
        return make_hit(
            rule_id="aug-assign",
            message="Prefer augmented assignment",
            path=path,
            before=code_for_small_stmt(node),
            after=code_for_small_stmt(aug),
        )
