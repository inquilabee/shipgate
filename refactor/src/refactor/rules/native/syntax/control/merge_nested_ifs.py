"""Merge nested ``if`` statements without ``elif``/``else``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import (
    BodyStatement,
    HitCollector,
    code_for_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class MergeNestedIfsRule:
    rule_id = "merge-nested-ifs"
    kind = RuleKind.REFACTOR
    summary = "Merge nested `if` statements into one condition"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, MergeNestedIfsRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
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
        return make_hit(
            rule_id="merge-nested-ifs",
            message="Merge nested if statements",
            path=path,
            before=code_for_stmt(cast("BodyStatement", outer)),
            after=code_for_stmt(cast("BodyStatement", merged)),
        )
