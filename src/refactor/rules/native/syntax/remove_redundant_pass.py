"""Remove ``pass`` statements that follow other statements in the same block."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    BodyStatement,
    ModuleAndIndentedBlockCollector,
    apply_with_transformer,
    body_cleanup_hit,
    detect_with_visitor,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class RemoveRedundantPassRule:
    rule_id = "remove-redundant-pass"
    kind = RuleKind.REFACTOR
    summary = "Remove redundant pass after other statements"
    apply_mode = ApplyMode.AUTO

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, RemoveRedundantPassRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, RemoveRedundantPassRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_Module(
            self,
            original_node: cst.Module,
            updated_node: cst.Module,
        ) -> cst.Module:
            _ = self, original_node
            cleaned = RemoveRedundantPassRule.body_without_redundant_passes(updated_node.body)
            return (
                updated_node
                if len(cleaned) == len(updated_node.body)
                else updated_node.with_changes(body=cleaned)
            )

        def leave_IndentedBlock(
            self,
            original_node: cst.IndentedBlock,
            updated_node: cst.IndentedBlock,
        ) -> cst.IndentedBlock:
            _ = self, original_node
            cleaned = RemoveRedundantPassRule.body_without_redundant_passes(updated_node.body)
            return (
                updated_node
                if len(cleaned) == len(updated_node.body)
                else updated_node.with_changes(body=cleaned)
            )

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
            if RemoveRedundantPassRule.is_docstring_stmt(stmt):
                continue
            saw_real_stmt = True

    @staticmethod
    def is_pass_stmt(stmt: cst.BaseStatement) -> bool:
        return (
            (False if len(stmt.body) != 1 else isinstance(stmt.body[0], cst.Pass))
            if isinstance(stmt, cst.SimpleStatementLine)
            else False
        )

    @staticmethod
    def is_docstring_stmt(stmt: cst.BaseStatement) -> bool:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return False
        expr = stmt.body[0]
        return isinstance(expr.value, cst.SimpleString) if isinstance(expr, cst.Expr) else False

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
                cleaned.append(stmt)
                continue
            if not RemoveRedundantPassRule.is_docstring_stmt(stmt):
                saw_real_stmt = True
            cleaned.append(stmt)
        return cleaned
