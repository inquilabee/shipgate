"""Native rule for ``reintroduce-else``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import (
    BodySequenceRewriteRule,
    single_terminal_stmt,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class ReintroduceElseRule(BodySequenceRewriteRule):
    rule_id = "reintroduce-else"
    summary = "Reintroduce else"
    message = "Move following statement into an else branch after terminal if"
    enabled = False

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
            if single_terminal_stmt(if_stmt.body) is None:
                continue
            return (
                [if_stmt, following],
                [
                    if_stmt.with_changes(
                        orelse=cst.Else(body=cst.IndentedBlock(body=[following])),
                    ),
                ],
            )
        return None
