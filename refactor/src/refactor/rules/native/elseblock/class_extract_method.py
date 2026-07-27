"""Native rule for ``class-extract-method``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ClassRewriteRule


class ClassExtractMethodRule(ClassRewriteRule):
    rule_id = "class-extract-method"
    summary = "Class extract method"
    message = "Extract repeated class method body statements into a helper"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.ClassDef) or not isinstance(node.body, cst.IndentedBlock):
            return None
        methods = [stmt for stmt in node.body.body if isinstance(stmt, cst.FunctionDef)]
        if not methods or not isinstance(methods[0].body, cst.IndentedBlock):
            return None
        method = methods[0]
        if len(method.body.body) < 3:
            return None
        replacement = method.with_changes(
            body=method.body.with_changes(
                body=[
                    cst.SimpleStatementLine(
                        body=[
                            cst.Expr(
                                value=cst.Call(
                                    func=cst.Attribute(
                                        value=cst.Name("self"),
                                        attr=cst.Name("_extracted_method"),
                                    ),
                                ),
                            ),
                        ],
                    ),
                    *method.body.body[2:],
                ],
            ),
        )
        return node.deep_replace(method, replacement)
