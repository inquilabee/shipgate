"""Native rule for ``swap-variable``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence


class SwapVariableRule(BodySequenceRewriteRule):
    rule_id = "swap-variable"
    summary = "Swap variable"
    message = "Use tuple unpacking to swap variables"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, first_stmt in enumerate(body[:-2]):
            second_stmt = body[index + 1]
            third_stmt = body[index + 2]
            swap = cls.swap_names(first_stmt, second_stmt, third_stmt)
            if swap is None:
                continue
            left_name, right_name = swap
            return (
                [first_stmt, second_stmt, third_stmt],
                [cls.swap_assignment(left_name, right_name)],
            )
        return None

    @classmethod
    def swap_names(
        cls,
        first_stmt: cst.BaseStatement,
        second_stmt: cst.BaseStatement,
        third_stmt: cst.BaseStatement,
    ) -> tuple[str, str] | None:
        first = cls.name_assign(first_stmt)
        second = cls.name_assign(second_stmt)
        third = cls.name_assign(third_stmt)
        if first is None or second is None or third is None:
            return None
        temp_name, left_value = first
        left_name, right_value = second
        right_name, temp_value = third
        if not isinstance(temp_value, cst.Name) or temp_value.value != temp_name:
            return None
        if not isinstance(left_value, cst.Name) or not isinstance(right_value, cst.Name):
            return None
        if left_value.value != left_name or right_value.value != right_name:
            return None
        return left_name, right_name

    @staticmethod
    def name_assign(stmt: cst.BaseStatement) -> tuple[str, cst.BaseExpression] | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        assign = stmt.body[0]
        if not isinstance(assign, cst.Assign) or len(assign.targets) != 1:
            return None
        target = assign.targets[0].target
        return (target.value, assign.value) if isinstance(target, cst.Name) else None

    @staticmethod
    def swap_assignment(left_name: str, right_name: str) -> cst.SimpleStatementLine:
        return cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[
                        cst.AssignTarget(
                            target=cst.Tuple(
                                elements=[
                                    cst.Element(value=cst.Name(left_name)),
                                    cst.Element(value=cst.Name(right_name)),
                                ],
                                lpar=[],
                                rpar=[],
                            ),
                        ),
                    ],
                    value=cst.Tuple(
                        elements=[
                            cst.Element(value=cst.Name(right_name)),
                            cst.Element(value=cst.Name(left_name)),
                        ],
                        lpar=[],
                        rpar=[],
                    ),
                ),
            ],
        )
