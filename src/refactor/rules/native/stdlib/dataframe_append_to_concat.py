"""Native rule for ``dataframe-append-to-concat``."""

from __future__ import annotations

import re

import libcst as cst

from refactor.protocol import RuleKind
from refactor.rules.native.expr_base import CallRewriteRule


class DataframeAppendToConcatRule(CallRewriteRule):
    rule_id = "dataframe-append-to-concat"
    kind = RuleKind.SUGGESTION
    summary = "Dataframe append to concat"
    message = "Use pandas.concat() instead of DataFrame.append()"
    DATAFRAME_NAME = re.compile(
        r"^(?:df|frame|dataframe|.*_(?:df|frame|dataframe))$",
        re.IGNORECASE,
    )

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "append":
            return None
        if not node.args or node.args[0].keyword is not None:
            return None
        if not cls._is_dataframe_receiver(node.func.value):
            return None
        return cst.Call(
            func=cst.Attribute(value=cst.Name("pd"), attr=cst.Name("concat")),
            args=[
                cst.Arg(
                    value=cst.List(
                        elements=[
                            cst.Element(value=node.func.value),
                            cst.Element(value=node.args[0].value),
                        ],
                    ),
                ),
            ],
        )

    @classmethod
    def _is_dataframe_receiver(cls, receiver: cst.BaseExpression) -> bool:
        return (
            cls.DATAFRAME_NAME.match(receiver.value) is not None
            if isinstance(receiver, cst.Name)
            else (
                cls.DATAFRAME_NAME.match(receiver.attr.value) is not None
                if isinstance(receiver, cst.Attribute)
                else False
            )
        )
