"""Native rule for ``use-itertools-product``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule, for_without_else_single_body


class UseItertoolsProductRule(ForRewriteRule):
    rule_id = "use-itertools-product"
    summary = "Use itertools product"
    message = "Use itertools.product for nested loops"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        match = for_without_else_single_body(node)
        if match is None:
            return None
        outer, inner = match
        if not isinstance(inner, cst.For) or inner.orelse is not None:
            return None
        return outer.with_changes(
            target=cst.Tuple(
                elements=[
                    cst.Element(value=outer.target),
                    cst.Element(value=inner.target),
                ],
                lpar=[],
                rpar=[],
            ),
            iter=cst.Call(
                func=cst.Attribute(value=cst.Name("itertools"), attr=cst.Name("product")),
                args=[cst.Arg(value=outer.iter), cst.Arg(value=inner.iter)],
            ),
            body=inner.body,
        )
