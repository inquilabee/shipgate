"""Native rule for ``merge-list-extend``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import (
    BodySequenceRewriteRule,
    method_call_stmt,
    same_method_target,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class MergeListExtendRule(BodySequenceRewriteRule):
    rule_id = "merge-list-extend"
    summary = "Merge list extend"
    message = "Merge adjacent literal list extends"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, left_stmt in enumerate(body[:-1]):
            right_stmt = body[index + 1]
            left = method_call_stmt(left_stmt, "extend")
            right = method_call_stmt(right_stmt, "extend")
            target = same_method_target(left, right)
            if target is None or left is None or right is None:
                continue
            if not cls.has_single_list_arg(left[1]) or not cls.has_single_list_arg(right[1]):
                continue
            left_list = left[1][0].value
            right_list = right[1][0].value
            if not isinstance(left_list, cst.List) or not isinstance(right_list, cst.List):
                continue
            return (
                [left_stmt, right_stmt],
                [
                    cst.SimpleStatementLine(
                        body=[
                            cst.Expr(
                                value=cst.Call(
                                    func=cst.Attribute(value=target, attr=cst.Name("extend")),
                                    args=[
                                        cst.Arg(
                                            value=left_list.with_changes(
                                                elements=[
                                                    *left_list.elements,
                                                    *right_list.elements,
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
    def has_single_list_arg(args: list[cst.Arg]) -> bool:
        return len(args) == 1 and args[0].keyword is None and isinstance(args[0].value, cst.List)
