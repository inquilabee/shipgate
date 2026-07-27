"""Native rule for ``use-dict-items``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule


class UseDictItemsRule(ForRewriteRule):
    rule_id = "use-dict-items"
    summary = "Use dict items"
    message = "Iterate over dictionary items when looking up each key"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.For) or not isinstance(node.target, cst.Name):
            return None
        if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) < 2:
            return None
        first = node.body.body[0]
        value_name = cls.lookup_assignment_name(first, node.target, node.iter)
        if value_name is None:
            return None
        return node.with_changes(
            target=cst.Tuple(
                elements=[
                    cst.Element(value=node.target),
                    cst.Element(value=cst.Name(value_name)),
                ],
                lpar=[],
                rpar=[],
            ),
            iter=cst.Call(
                func=cst.Attribute(value=node.iter, attr=cst.Name("items")),
                args=[],
            ),
            body=node.body.with_changes(body=node.body.body[1:]),
        )

    @staticmethod
    def lookup_assignment_name(
        stmt: cst.BaseStatement,
        key_name: cst.Name,
        mapping: cst.BaseExpression,
    ) -> str | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        assign = stmt.body[0]
        if not isinstance(assign, cst.Assign) or len(assign.targets) != 1:
            return None
        target = assign.targets[0].target
        if not isinstance(target, cst.Name):
            return None
        if not isinstance(assign.value, cst.Subscript) or not assign.value.value.deep_equals(
            mapping,
        ):
            return None
        if len(assign.value.slice) != 1 or not isinstance(assign.value.slice[0].slice, cst.Index):
            return None
        index = assign.value.slice[0].slice.value
        return target.value if index.deep_equals(key_name) else None
