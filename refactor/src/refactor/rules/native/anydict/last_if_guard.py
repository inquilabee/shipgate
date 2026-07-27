"""Native rule for ``last-if-guard``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule, negated_expr

if TYPE_CHECKING:
    from collections.abc import Sequence


class LastIfGuardRule(BodySequenceRewriteRule):
    rule_id = "last-if-guard"
    summary = "Last if guard"
    message = "Use a guard clause before the final fallback statement"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, if_stmt in enumerate(body[:-1]):
            following = body[index + 1]
            if not isinstance(if_stmt, cst.If) or if_stmt.orelse is not None:
                continue
            if not isinstance(if_stmt.body, cst.IndentedBlock):
                continue
            return (
                [if_stmt, following],
                [
                    cst.If(
                        test=negated_expr(if_stmt.test),
                        body=cst.IndentedBlock(body=[following]),
                    ),
                    *if_stmt.body.body,
                ],
            )
        return None
