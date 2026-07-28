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
        assign = UseDictItemsRule.simple_name_assign(stmt)
        if assign is None:
            return None
        target, value = assign
        if not UseDictItemsRule.subscript_lookup_for_key(value, mapping, key_name):
            return None
        return target

    @staticmethod
    def simple_name_assign(
        stmt: cst.BaseStatement,
    ) -> tuple[str, cst.BaseExpression] | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        assign = stmt.body[0]
        if not isinstance(assign, cst.Assign) or len(assign.targets) != 1:
            return None
        target = assign.targets[0].target
        return (target.value, assign.value) if isinstance(target, cst.Name) else None

    @staticmethod
    def subscript_lookup_for_key(
        value: cst.BaseExpression,
        mapping: cst.BaseExpression,
        key_name: cst.Name,
    ) -> bool:
        return (
            False
            if not isinstance(value, cst.Subscript) or not value.value.deep_equals(mapping)
            else (
                False
                if len(value.slice) != 1 or not isinstance(value.slice[0].slice, cst.Index)
                else value.slice[0].slice.value.deep_equals(key_name)
            )
        )
