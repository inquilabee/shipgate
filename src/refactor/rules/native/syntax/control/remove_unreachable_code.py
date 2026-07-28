"""Flag statements after ``return``, ``raise``, ``break``, or ``continue``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    BodyStatement,
    ModuleAndIndentedBlockCollector,
    body_cleanup_hit,
    detect_with_visitor,
    noop_apply,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class RemoveUnreachableCodeRule:
    rule_id = "remove-unreachable-code"
    kind = RuleKind.REFACTOR
    summary = "Remove unreachable code after return/raise/break/continue"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, RemoveUnreachableCodeRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(ModuleAndIndentedBlockCollector):
        def __init__(self, *, path: str) -> None:
            super().__init__(path=path, checker=RemoveUnreachableCodeRule.check_block)

        def visit_SimpleStatementLine(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.SimpleStatementLine,
        ) -> bool:
            RemoveUnreachableCodeRule.check_simple_line(node, self.hits, self.path)
            return True

    @staticmethod
    def check_block(
        body: Sequence[cst.BaseStatement],
        hits: list[Hit],
        path: str,
    ) -> None:
        for index, stmt in enumerate(body):
            if not RemoveUnreachableCodeRule.is_terminal(stmt):
                continue
            hits.extend(
                RemoveUnreachableCodeRule.hit_for(unreachable, body, path)
                for unreachable in body[index + 1 :]
            )

    @staticmethod
    def check_simple_line(
        line: cst.SimpleStatementLine,
        hits: list[Hit],
        path: str,
    ) -> None:
        for index, small_stmt in enumerate(line.body):
            if not RemoveUnreachableCodeRule.is_terminal_stmt(small_stmt):
                continue
            hits.extend(
                RemoveUnreachableCodeRule.hit_for(
                    cst.SimpleStatementLine(body=[unreachable]),
                    [cst.SimpleStatementLine(body=[small_stmt])],
                    path,
                )
                for unreachable in line.body[index + 1 :]
            )

    @staticmethod
    def is_terminal(stmt: cst.BaseStatement) -> bool:
        return (
            (
                False
                if len(stmt.body) != 1
                else RemoveUnreachableCodeRule.is_terminal_stmt(stmt.body[0])
            )
            if isinstance(stmt, cst.SimpleStatementLine)
            else False
        )

    @staticmethod
    def is_terminal_stmt(stmt: cst.BaseSmallStatement) -> bool:
        return isinstance(stmt, (cst.Return, cst.Raise, cst.Break, cst.Continue))

    @staticmethod
    def hit_for(
        stmt: cst.BaseStatement,
        body: Sequence[cst.BaseStatement],
        path: str,
    ) -> Hit:
        return body_cleanup_hit(
            rule_id="remove-unreachable-code",
            message="Unreachable code after control-flow exit",
            path=path,
            stmt=stmt,
            cleaned_body=RemoveUnreachableCodeRule.body_without_unreachable(body),
        )

    @staticmethod
    def body_without_unreachable(
        body: Sequence[cst.BaseStatement],
    ) -> list[BodyStatement]:
        cleaned: list[BodyStatement] = []
        exited = False
        for stmt in body:
            if exited:
                continue
            cleaned.append(stmt)
            if RemoveUnreachableCodeRule.is_terminal(stmt):
                exited = True
        return cleaned
