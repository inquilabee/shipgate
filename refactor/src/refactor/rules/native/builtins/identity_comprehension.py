"""Replace identity list comprehensions with ``list()``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class IdentityComprehensionRule:
    rule_id = "identity-comprehension"
    kind = RuleKind.REFACTOR
    summary = "Replace `[x for x in xs]` with `list(xs)`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = IdentityComprehensionRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_ListComp(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.ListComp,
        ) -> bool:
            match = IdentityComprehensionRule.match_identity(node)
            if match is None:
                return True
            self.hits.append(IdentityComprehensionRule.hit_for(node, match, self.path))
            return True

    @staticmethod
    def match_identity(node: cst.ListComp) -> cst.BaseExpression | None:
        if not isinstance(node.elt, cst.Name):
            return None
        for_in = node.for_in
        if not isinstance(for_in, cst.CompFor):
            return None
        if for_in.inner_for_in is not None:
            return None
        if for_in.ifs:
            return None
        if not isinstance(for_in.target, cst.Name):
            return None
        if for_in.target.value != node.elt.value:
            return None
        return for_in.iter

    @staticmethod
    def hit_for(
        node: cst.ListComp,
        iterable: cst.BaseExpression,
        path: str,
    ) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=node)])]
        ).code.strip()
        list_call = cst.Call(func=cst.Name("list"), args=[cst.Arg(value=iterable)])
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=list_call)])]
        ).code.strip()
        return Hit(
            rule_id="identity-comprehension",
            message="Prefer `list(xs)` over identity comprehension",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
