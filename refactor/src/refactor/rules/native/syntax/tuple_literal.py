"""Replace empty ``tuple()`` with ``()``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class TupleLiteralRule:
    rule_id = "tuple-literal"
    kind = RuleKind.REFACTOR
    summary = "Replace empty `tuple()` with `()`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = TupleLiteralRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_Call(self, node: cst.Call) -> bool:  # ruff:ignore[invalid-function-name]
            if not TupleLiteralRule.is_empty_tuple_call(node):
                return True
            self.hits.append(TupleLiteralRule.hit_for(node, self.path))
            return True

    @staticmethod
    def is_empty_tuple_call(node: cst.Call) -> bool:
        return isinstance(node.func, cst.Name) and node.func.value == "tuple" and not node.args

    @staticmethod
    def hit_for(node: cst.Call, path: str) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=node)])]
        ).code.strip()
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=cst.Tuple(elements=[]))])]
        ).code.strip()
        return Hit(
            rule_id="tuple-literal",
            message="Prefer `()` over empty tuple()",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
