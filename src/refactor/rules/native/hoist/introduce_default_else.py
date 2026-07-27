"""Native rule for ``introduce-default-else``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import (
    BodySequenceRewriteRule,
    single_assign_from_stmt,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class IntroduceDefaultElseRule(BodySequenceRewriteRule):
    rule_id = "introduce-default-else"
    summary = "Introduce default else"
    message = "Move default assignment into an explicit else branch"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, default_stmt in enumerate(body[:-1]):
            if_stmt = body[index + 1]
            default_assign = single_assign_from_stmt(default_stmt)
            if not isinstance(if_stmt, cst.If) or if_stmt.orelse is not None:
                continue
            if not isinstance(if_stmt.body, cst.IndentedBlock) or len(if_stmt.body.body) != 1:
                continue
            branch_assign = single_assign_from_stmt(if_stmt.body.body[0])
            if default_assign is None or branch_assign is None:
                continue
            if not default_assign.targets[0].target.deep_equals(branch_assign.targets[0].target):
                continue
            else_stmt = cst.SimpleStatementLine(body=[default_assign])
            return (
                [default_stmt, if_stmt],
                [
                    if_stmt.with_changes(
                        orelse=cst.Else(body=cst.IndentedBlock(body=[else_stmt])),
                    ),
                ],
            )
        return None
