"""Replace identity list comprehensions with ``list()``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    detect_with_visitor,
    expr_replacement_hit,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class IdentityComprehensionRule:
    rule_id = "identity-comprehension"
    kind = RuleKind.REFACTOR
    summary = "Replace `[x for x in xs]` with `list(xs)`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, IdentityComprehensionRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
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
        list_call = cst.Call(func=cst.Name("list"), args=[cst.Arg(value=iterable)])
        return expr_replacement_hit(
            rule_id="identity-comprehension",
            message="Prefer `list(xs)` over identity comprehension",
            path=path,
            before_expr=node,
            after_expr=list_call,
        )
