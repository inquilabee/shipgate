"""Remove ``assert True`` statements (optionally with a message)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import BodyStatement, is_true
from refactor.rules.native.expr_base import BodyCleanupRule

if TYPE_CHECKING:
    from collections.abc import Sequence


class RemoveAssertTrueRule(BodyCleanupRule):
    rule_id = "remove-assert-true"
    summary = "Remove `assert True` statements"
    message = "Remove assert True"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[cst.BaseStatement, Sequence[BodyStatement]] | None:
        for stmt in body:
            if not cls.is_assert_true_stmt(stmt):
                continue
            return stmt, cls.body_without_assert_true(body)
        return None

    @staticmethod
    def is_assert_true_stmt(stmt: cst.BaseStatement) -> bool:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return False
        small = stmt.body[0]
        return isinstance(small, cst.Assert) and is_true(small.test)

    @staticmethod
    def body_without_assert_true(
        body: Sequence[cst.BaseStatement],
    ) -> list[BodyStatement]:
        cleaned: list[BodyStatement] = []
        for stmt in body:
            if RemoveAssertTrueRule.is_assert_true_stmt(stmt):
                continue
            cleaned.append(cast("BodyStatement", stmt))
        return cleaned
