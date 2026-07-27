"""Native rule for ``remove-empty-nested-block``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.expr_base import BodyCleanupRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


class RemoveEmptyNestedBlockRule(BodyCleanupRule):
    rule_id = "remove-empty-nested-block"
    summary = "Remove empty nested block"
    message = "Remove an empty nested block"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[cst.BaseStatement, Sequence[BodyStatement]] | None:
        for index, stmt in enumerate(body):
            if cls.is_empty_compound(stmt):
                cleaned = [cast("BodyStatement", item) for item in body if item is not stmt]
                return body[index], cleaned
        return None

    @staticmethod
    def is_empty_compound(stmt: cst.BaseStatement) -> bool:
        if not isinstance(stmt, cst.BaseCompoundStatement):
            return False
        if not isinstance(stmt.body, cst.IndentedBlock) or len(stmt.body.body) != 1:
            return False
        inner = stmt.body.body[0]
        return (
            isinstance(inner, cst.SimpleStatementLine)
            and len(inner.body) == 1
            and isinstance(inner.body[0], cst.Pass)
        )
