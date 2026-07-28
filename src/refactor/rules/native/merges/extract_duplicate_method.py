"""Native rule for ``extract-duplicate-method``."""

from __future__ import annotations

from typing import cast

import libcst as cst

from refactor.rules.native.stmt_base import ClassRewriteRule


class ExtractDuplicateMethodRule(ClassRewriteRule):
    rule_id = "extract-duplicate-method"
    summary = "Extract duplicate method"
    message = "Replace duplicate method bodies with a shared helper call"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.ClassDef) or not isinstance(node.body, cst.IndentedBlock):
            return None
        methods = [
            stmt
            for stmt in node.body.body
            if isinstance(stmt, cst.FunctionDef) and not cls._is_stub_method(stmt)
        ]
        for index, left in enumerate(methods[:-1]):
            right = methods[index + 1]
            if cls._skip_duplicate_pair(left, right):
                continue
            if not left.body.deep_equals(right.body):
                continue
            replacement = right.with_changes(
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.Return(
                                    value=cst.Call(
                                        func=cst.Attribute(
                                            value=cst.Name("self"),
                                            attr=cst.Name(left.name.value),
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            )
            return node.deep_replace(right, replacement)
        return None

    @staticmethod
    def _method_body_statements(method: cst.FunctionDef) -> tuple[cst.BaseStatement, ...]:
        body = method.body
        return cast(
            "tuple[cst.BaseStatement, ...]",
            tuple(body.body)
            if isinstance(body, cst.IndentedBlock | cst.SimpleStatementSuite)
            else (),
        )

    @classmethod
    def _is_stub_method(cls, method: cst.FunctionDef) -> bool:
        statements = cls._method_body_statements(method)
        if len(statements) != 1:
            return False
        stmt = statements[0]
        if isinstance(stmt, cst.Expr) and isinstance(stmt.value, cst.Ellipsis):
            return True
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return False
        small = stmt.body[0]
        if not isinstance(small, cst.Raise):
            return False
        exc = small.exc
        return isinstance(exc, cst.Name) and exc.value == "NotImplementedError"

    @staticmethod
    def _skip_duplicate_pair(left: cst.FunctionDef, right: cst.FunctionDef) -> bool:
        left_name = left.name.value
        right_name = right.name.value
        return (left_name.startswith("visit_") and right_name.startswith("visit_")) or (
            left_name.startswith("leave_") and right_name.startswith("leave_")
        )
