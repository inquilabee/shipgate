"""Native rule for ``merge-dict-assign``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence


class MergeDictAssignRule(BodySequenceRewriteRule):
    rule_id = "merge-dict-assign"
    summary = "Merge dict assign"
    message = "Merge adjacent dictionary item assignments"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, left_stmt in enumerate(body[:-1]):
            right_stmt = body[index + 1]
            left = cls.dict_item_assign(left_stmt)
            right = cls.dict_item_assign(right_stmt)
            if left is None or right is None:
                continue
            target, left_key, left_value = left
            right_target, right_key, right_value = right
            if not target.deep_equals(right_target):
                continue
            return (
                [left_stmt, right_stmt],
                [
                    cst.SimpleStatementLine(
                        body=[
                            cst.Expr(
                                value=cst.Call(
                                    func=cst.Attribute(value=target, attr=cst.Name("update")),
                                    args=[
                                        cst.Arg(
                                            value=cst.Dict(
                                                elements=[
                                                    cst.DictElement(
                                                        key=left_key,
                                                        value=left_value,
                                                    ),
                                                    cst.DictElement(
                                                        key=right_key,
                                                        value=right_value,
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ],
            )
        return None

    @staticmethod
    def dict_item_assign(
        stmt: cst.BaseStatement,
    ) -> tuple[cst.BaseExpression, cst.BaseExpression, cst.BaseExpression] | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        assign = stmt.body[0]
        if not isinstance(assign, cst.Assign) or len(assign.targets) != 1:
            return None
        target = assign.targets[0].target
        if not isinstance(target, cst.Subscript) or len(target.slice) != 1:
            return None
        subscript = target.slice[0].slice
        if not isinstance(subscript, cst.Index):
            return None
        return target.value, subscript.value, assign.value
