"""Native rule for ``remove-unnecessary-cast``."""

from __future__ import annotations

import libcst as cst
from libcst.metadata import ParentNodeProvider

from refactor.cst_util import HitCollector
from refactor.rules.native.expr_base import CallRewriteRule


class RemoveUnnecessaryCastRule(CallRewriteRule):
    rule_id = "remove-unnecessary-cast"
    summary = "Remove unnecessary cast"
    message = "Remove redundant typing.cast around a value"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not cls.is_cast_func(node.func):
            return None
        if len(node.args) != 2 or any(arg.keyword is not None for arg in node.args):
            return None
        annotation = node.args[0].value
        if isinstance(annotation, cst.SimpleString):
            return None
        return node.args[1].value

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        class RemoveUnnecessaryCastFinder(HitCollector):
            METADATA_DEPENDENCIES = (
                *HitCollector.METADATA_DEPENDENCIES,
                ParentNodeProvider,
            )

            def visit_Call(
                self,
                node: cst.Call,
            ) -> bool:
                replacement = cls.match(node)
                if replacement is None:
                    return True
                try:
                    parent = self.get_metadata(ParentNodeProvider, node)
                except KeyError:
                    parent = None
                if isinstance(parent, cst.Attribute) and parent.value is node:
                    return True
                self.record_hit(cls.hit_for(node, replacement, self.path), node)
                return True

        return RemoveUnnecessaryCastFinder

    @staticmethod
    def is_cast_func(node: cst.BaseExpression) -> bool:
        return (
            node.value == "cast"
            if isinstance(node, cst.Name)
            else (
                isinstance(node, cst.Attribute)
                and isinstance(node.value, cst.Name)
                and node.value.value == "typing"
                and node.attr.value == "cast"
            )
        )
