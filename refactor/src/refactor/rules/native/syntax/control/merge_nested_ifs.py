"""Merge nested ``if`` statements without ``elif``/``else``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

BodyStatement = cst.SimpleStatementLine | cst.BaseCompoundStatement

if TYPE_CHECKING:
    from collections.abc import Sequence


class MergeNestedIfsRule:
    rule_id = "merge-nested-ifs"
    kind = RuleKind.REFACTOR
    summary = "Merge nested `if` statements into one condition"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = MergeNestedIfsRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_If(self, node: cst.If) -> bool:  # ruff:ignore[invalid-function-name]
            match = MergeNestedIfsRule.match_nested_ifs(node)
            if match is not None:
                outer, merged = match
                self.hits.append(MergeNestedIfsRule.hit_for(outer, merged, self.path))
            return True

    @staticmethod
    def match_nested_ifs(node: cst.If) -> tuple[cst.If, cst.If] | None:
        if node.orelse is not None:
            return None
        if len(node.body.body) != 1:
            return None
        inner = node.body.body[0]
        if not isinstance(inner, cst.If):
            return None
        if inner.orelse is not None:
            return None
        merged_test = cst.BooleanOperation(
            left=node.test,
            operator=cst.And(),
            right=inner.test,
        )
        merged = cst.If(test=merged_test, body=inner.body)
        return node, merged

    @staticmethod
    def hit_for(outer: cst.If, merged: cst.If, path: str) -> Hit:
        before = cst.Module(body=[cast("BodyStatement", outer)]).code.strip()
        after = cst.Module(body=[cast("BodyStatement", merged)]).code.strip()
        return Hit(
            rule_id="merge-nested-ifs",
            message="Merge nested if statements",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
