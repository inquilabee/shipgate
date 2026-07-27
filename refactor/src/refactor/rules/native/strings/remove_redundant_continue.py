"""Native rule for ``remove-redundant-continue``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.expr_base import BodyCleanupRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


class RemoveRedundantContinueRule(BodyCleanupRule):
    rule_id = "remove-redundant-continue"
    summary = "Remove redundant continue"
    message = "Remove a redundant trailing continue"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[cst.BaseStatement, Sequence[BodyStatement]] | None:
        if not body or not cls.is_continue_stmt(body[-1]):
            return None
        return body[-1], [cast("BodyStatement", stmt) for stmt in body[:-1]]

    @staticmethod
    def is_continue_stmt(stmt: cst.BaseStatement) -> bool:
        return (
            isinstance(stmt, cst.SimpleStatementLine)
            and len(stmt.body) == 1
            and isinstance(stmt.body[0], cst.Continue)
        )
