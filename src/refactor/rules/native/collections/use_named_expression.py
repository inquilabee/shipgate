"""Native rule for ``use-named-expression``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import (
    BodySequenceRewriteRule,
    ReturnAssignedExpressionRule,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class UseNamedExpressionRule(BodySequenceRewriteRule):
    rule_id = "use-named-expression"
    summary = "Use named expression"
    message = "Use a named expression in the following condition"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, assign_stmt in enumerate(body[:-1]):
            if_stmt = body[index + 1]
            assignment = ReturnAssignedExpressionRule.name_assign_stmt(assign_stmt)
            if assignment is None or not isinstance(if_stmt, cst.If):
                continue
            target_name, value = assignment
            if not isinstance(if_stmt.test, cst.Name) or if_stmt.test.value != target_name:
                continue
            return (
                [assign_stmt, if_stmt],
                [
                    if_stmt.with_changes(
                        test=cst.NamedExpr(target=cst.Name(target_name), value=value),
                    ),
                ],
            )
        return None
