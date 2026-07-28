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
        """True when ``len(...)`` is used as a boolean, not as a numeric count."""
        return (
            parent is not None
            and not cls.count_valued_parent(parent)
            and cls.bool_valued_parent(node, parent)
        )

    @staticmethod
    def count_valued_parent(parent: cst.CSTNode) -> bool:
        # Count-valued uses (return/assign) need the integer length, not bool(...).
        return isinstance(
            parent,
            (
                cst.Assign,
                cst.AnnAssign,
                cst.AugAssign,
                cst.Return,
                cst.Comparison,
                cst.BinaryOperation,
                cst.Arg,
                cst.Subscript,
                cst.Slice,
                cst.Call,
                cst.CompFor,
            ),
        )

    @staticmethod
    def bool_valued_parent(node: cst.Call, parent: cst.CSTNode) -> bool:
        match parent:
            case cst.If(test=test) | cst.While(test=test):
                return test is node
            case cst.BooleanOperation():
                return True
            case cst.UnaryOperation(operator=cst.Not()):
                return True
            case cst.NamedExpr():
                return True
            case _:
                return False

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
