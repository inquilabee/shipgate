"""Native rule for ``extract-duplicate-method``."""

from __future__ import annotations

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
        methods = [stmt for stmt in node.body.body if isinstance(stmt, cst.FunctionDef)]
        for index, left in enumerate(methods[:-1]):
            right = methods[index + 1]
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
