"""Remove ``pass`` statements that follow other statements in the same block."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import (
    BodyStatement,
    ModuleAndIndentedBlockCollector,
    body_cleanup_hit,
    detect_with_visitor,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class RemoveRedundantPassRule:
    rule_id = "remove-redundant-pass"
    kind = RuleKind.REFACTOR
    summary = "Remove redundant pass after other statements"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, RemoveRedundantPassRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(ModuleAndIndentedBlockCollector):
        def __init__(self, *, path: str) -> None:
            super().__init__(path=path, checker=RemoveRedundantPassRule.check_body)

    @staticmethod
    def check_body(
        body: Sequence[cst.BaseStatement],
        hits: list[Hit],
        path: str,
    ) -> None:
        saw_real_stmt = False
        for stmt in body:
            if RemoveRedundantPassRule.is_pass_stmt(stmt):
                if saw_real_stmt:
                    hits.append(RemoveRedundantPassRule.hit_for(stmt, body, path))
                continue
            saw_real_stmt = True

    @staticmethod
    def is_pass_stmt(stmt: cst.BaseStatement) -> bool:
        if not isinstance(stmt, cst.SimpleStatementLine):
            return False
        if len(stmt.body) != 1:
            return False
        return isinstance(stmt.body[0], cst.Pass)

    @staticmethod
    def hit_for(
        stmt: cst.BaseStatement,
        body: Sequence[cst.BaseStatement],
        path: str,
    ) -> Hit:
        return body_cleanup_hit(
            rule_id="remove-redundant-pass",
            message="Remove redundant pass",
            path=path,
            stmt=stmt,
            cleaned_body=RemoveRedundantPassRule.body_without_redundant_passes(body),
        )

    @staticmethod
    def body_without_redundant_passes(
        body: Sequence[cst.BaseStatement],
    ) -> list[BodyStatement]:
        cleaned: list[BodyStatement] = []
        saw_real_stmt = False
        for stmt in body:
            if RemoveRedundantPassRule.is_pass_stmt(stmt):
                if saw_real_stmt:
                    continue
                cleaned.append(cast("BodyStatement", stmt))
                continue
            saw_real_stmt = True
            cleaned.append(cast("BodyStatement", stmt))
        return cleaned
