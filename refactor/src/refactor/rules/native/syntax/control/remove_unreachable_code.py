"""Flag statements after ``return``, ``raise``, ``break``, or ``continue``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

BodyStatement = cst.SimpleStatementLine | cst.BaseCompoundStatement

if TYPE_CHECKING:
    from collections.abc import Sequence


class RemoveUnreachableCodeRule:
    rule_id = "remove-unreachable-code"
    kind = RuleKind.REFACTOR
    summary = "Remove unreachable code after return/raise/break/continue"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = RemoveUnreachableCodeRule.Finder(path=path)
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
            RemoveUnreachableCodeRule.check_block(node.body, self.hits, self.path)
            return True

        def visit_IndentedBlock(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.IndentedBlock,
        ) -> bool:
            RemoveUnreachableCodeRule.check_block(node.body, self.hits, self.path)
            return True

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
        if not isinstance(stmt, cst.SimpleStatementLine):
            return False
        if len(stmt.body) != 1:
            return False
        return RemoveUnreachableCodeRule.is_terminal_stmt(stmt.body[0])

    @staticmethod
    def is_terminal_stmt(stmt: cst.BaseSmallStatement) -> bool:
        return isinstance(stmt, (cst.Return, cst.Raise, cst.Break, cst.Continue))

    @staticmethod
    def hit_for(
        stmt: cst.BaseStatement,
        body: Sequence[cst.BaseStatement],
        path: str,
    ) -> Hit:
        before = cst.Module(body=[cast("BodyStatement", stmt)]).code.strip()
        cleaned = RemoveUnreachableCodeRule.body_without_unreachable(body)
        after = cst.Module(body=cleaned).code.strip()
        return Hit(
            rule_id="remove-unreachable-code",
            message="Unreachable code after control-flow exit",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
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
            cleaned.append(cast("BodyStatement", stmt))
            if RemoveUnreachableCodeRule.is_terminal(stmt):
                exited = True
        return cleaned
