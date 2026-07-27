"""Native rule for ``remove-pass-body``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.expr_base import BodyCleanupRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


class RemovePassBodyRule(BodyCleanupRule):
    rule_id = "remove-pass-body"
    summary = "Remove pass body"
    message = "Remove a pass-only body"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[cst.BaseStatement, Sequence[BodyStatement]] | None:
        return (body[0], []) if len(body) == 1 and cls.is_pass_stmt(body[0]) else None

    @staticmethod
    def is_pass_stmt(stmt: cst.BaseStatement) -> bool:
        return (
            isinstance(stmt, cst.SimpleStatementLine)
            and len(stmt.body) == 1
            and isinstance(stmt.body[0], cst.Pass)
        )
