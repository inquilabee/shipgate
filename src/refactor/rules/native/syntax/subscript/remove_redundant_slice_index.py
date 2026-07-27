"""Simplify redundant slice bounds like ``xs[0:n]`` and ``xs[n:None]``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import is_none_name
from refactor.rules.native.expr_base import SubscriptRewriteRule


class RemoveRedundantSliceIndexRule(SubscriptRewriteRule):
    rule_id = "remove-redundant-slice-index"
    summary = "Remove redundant slice start/stop indices"
    message = "Remove redundant slice index"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Subscript):
            return None
        if len(node.slice) != 1:
            return None
        element = node.slice[0]
        if not isinstance(element.slice, cst.Slice):
            return None
        simplified = cls.simplified_slice(element.slice)
        if simplified is None:
            return None
        return node.with_changes(slice=[element.with_changes(slice=simplified)])

    @staticmethod
    def simplified_slice(slice_node: cst.Slice) -> cst.Slice | None:
        if isinstance(slice_node.lower, cst.Integer) and slice_node.lower.value == "0":
            return slice_node.with_changes(lower=None)
        if slice_node.upper is not None and is_none_name(slice_node.upper):
            return slice_node.with_changes(upper=None)
        return None
