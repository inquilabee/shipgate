"""Native rule for ``lift-return-into-if``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import BodySequenceRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence


class LiftReturnIntoIfRule(BodySequenceRewriteRule):
    rule_id = "lift-return-into-if"
    summary = "Lift return into if"
    message = "Lift a following return into an if else branch"

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
            if not isinstance(single_small_stmt(if_stmt.body), cst.Return):
                continue
            if not isinstance(following, cst.SimpleStatementLine) or len(following.body) != 1:
                continue
            if not isinstance(following.body[0], cst.Return):
                continue
            return (
                [if_stmt, following],
                [if_stmt.with_changes(orelse=cst.Else(body=cst.IndentedBlock(body=[following])))],
            )
        return None
