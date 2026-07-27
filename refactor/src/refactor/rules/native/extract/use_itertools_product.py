"""Native rule for ``use-itertools-product``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule


class UseItertoolsProductRule(ForRewriteRule):
    rule_id = "use-itertools-product"
    summary = "Use itertools product"
    message = "Use itertools.product for nested loops"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.For) or node.orelse is not None:
            return None
        if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) != 1:
            return None
        inner = node.body.body[0]
        if not isinstance(inner, cst.For) or inner.orelse is not None:
            return None
        return node.with_changes(
            target=cst.Tuple(
                elements=[
                    cst.Element(value=node.target),
                    cst.Element(value=inner.target),
                ],
                lpar=[],
                rpar=[],
            ),
            iter=cst.Call(
                func=cst.Attribute(value=cst.Name("itertools"), attr=cst.Name("product")),
                args=[cst.Arg(value=node.iter), cst.Arg(value=inner.iter)],
            ),
            body=inner.body,
        )
