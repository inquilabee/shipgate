"""Native rule for ``collection-to-bool``."""

from __future__ import annotations

import libcst as cst
from libcst.metadata import ParentNodeProvider, PositionProvider

from refactor.cst_util import HitCollector
from refactor.rules.native.expr_base import CallRewriteRule


class CollectionToBoolRule(CallRewriteRule):
    rule_id = "collection-to-bool"
    summary = "Collection to bool"
    message = "Use bool(collection) when an explicit boolean value is needed"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return (
            (
                None
                if not isinstance(node.func, cst.Name) or node.func.value != "len"
                else (
                    None
                    if len(node.args) != 1 or node.args[0].keyword is not None
                    else cst.Call(
                        func=cst.Name("bool"),
                        args=[cst.Arg(value=node.args[0].value)],
                    )
                )
            )
            if isinstance(node, cst.Call)
            else None
        )

    @classmethod
    def truthiness_len(cls, node: cst.Call, parent: cst.CSTNode | None) -> bool:
        return (
            False
            if parent is None
            else (
                False
                if isinstance(parent, cst.Comparison)
                else (
                    False
                    if isinstance(
                        parent,
                        (cst.Arg, cst.Subscript, cst.Slice, cst.Call, cst.CompFor),
                    )
                    else (
                        False
                        if isinstance(parent, cst.BinaryOperation)
                        else (
                            True
                            if isinstance(parent, (cst.Assign, cst.AnnAssign, cst.Return))
                            else (
                                parent.test is node
                                if isinstance(parent, cst.If)
                                else (
                                    parent.test is node
                                    if isinstance(parent, cst.While)
                                    else (
                                        True
                                        if isinstance(parent, (cst.BooleanOperation,))
                                        else (
                                            True
                                            if isinstance(parent, cst.UnaryOperation)
                                            and isinstance(parent.operator, cst.Not)
                                            else isinstance(parent, cst.NamedExpr)
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            METADATA_DEPENDENCIES = (PositionProvider, ParentNodeProvider)

            def visit_Call(self, node: cst.Call) -> bool:  # ruff:ignore[invalid-function-name]
                replacement = rule.match(node)
                if replacement is None:
                    return True
                parent = self.get_metadata(ParentNodeProvider, node)
                if not rule.truthiness_len(node, parent):
                    return True
                self.record_hit(rule.hit_for(node, replacement, self.path), node)
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder
