"""Remove ``pass`` statements that follow other statements in the same block."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

BodyStatement = cst.SimpleStatementLine | cst.BaseCompoundStatement

if TYPE_CHECKING:
    from collections.abc import Sequence


class RemoveRedundantPassRule:
    rule_id = "remove-redundant-pass"
    kind = RuleKind.REFACTOR
    summary = "Remove redundant pass after other statements"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = RemoveRedundantPassRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_Module(self, node: cst.Module) -> bool:  # ruff:ignore[invalid-function-name]
            RemoveRedundantPassRule.check_body(node.body, self.hits, self.path)
            return True

        def visit_IndentedBlock(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.IndentedBlock,
        ) -> bool:
            RemoveRedundantPassRule.check_body(node.body, self.hits, self.path)
            return True

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
        before = cst.Module(body=[cast("BodyStatement", stmt)]).code.strip()
        cleaned = RemoveRedundantPassRule.body_without_redundant_passes(body)
        after = cst.Module(body=cleaned).code.strip()
        return Hit(
            rule_id="remove-redundant-pass",
            message="Remove redundant pass",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
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
