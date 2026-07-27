"""Replace ``d[k] if k in d else v`` with ``d.get(k, v)``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    apply_with_transformer,
    code_for_expr,
    detect_with_visitor,
    make_hit,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


@dataclass(frozen=True)
class DefaultGetParts:
    mapping: cst.BaseExpression
    key: cst.BaseExpression
    default: cst.BaseExpression


class DefaultGetRule:
    rule_id = "default-get"
    kind = RuleKind.REFACTOR
    summary = "Replace `d[k] if k in d else v` with `d.get(k, v)`"
    safe_apply = True

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, DefaultGetRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, DefaultGetRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_IfExp(  # ruff:ignore[invalid-function-name]
            self,
            original_node: cst.IfExp,
            updated_node: cst.IfExp,
        ) -> cst.BaseExpression:
            _ = self, original_node
            parts = DefaultGetRule.match_parts(updated_node)
            if parts is None:
                return updated_node
            return DefaultGetRule.build_get_call(parts)

    class Finder(HitCollector):
        def visit_IfExp(self, node: cst.IfExp) -> bool:  # ruff:ignore[invalid-function-name]
            parts = DefaultGetRule.match_parts(node)
            if parts is None:
                return True
            self.record_hit(DefaultGetRule.hit_for(parts, node, self.path), node)
            return True

    @staticmethod
    def hit_for(parts: DefaultGetParts, node: cst.IfExp, path: str) -> Hit:
        after_expr = DefaultGetRule.build_get_call(parts)
        return make_hit(
            rule_id="default-get",
            message="Prefer dict.get over membership ternary",
            path=path,
            before=code_for_expr(node),
            after=code_for_expr(after_expr),
        )

    @staticmethod
    def match_parts(node: cst.IfExp) -> DefaultGetParts | None:
        mapping_key = DefaultGetRule.membership_map_key(node)
        if mapping_key is None:
            return None
        mapping, key = mapping_key
        if not isinstance(node.body, cst.Subscript):
            return None
        if not node.body.value.deep_equals(mapping):
            return None
        key_node = DefaultGetRule.subscript_key(node.body)
        if key_node is None or not key_node.deep_equals(key):
            return None
        return DefaultGetParts(mapping=mapping, key=key, default=node.orelse)

    @staticmethod
    def membership_map_key(
        node: cst.IfExp,
    ) -> tuple[cst.BaseExpression, cst.BaseExpression] | None:
        if not isinstance(node.test, cst.Comparison):
            return None
        if len(node.test.comparisons) != 1:
            return None
        target = node.test.comparisons[0]
        if not isinstance(target.operator, cst.In):
            return None
        return target.comparator, node.test.left

    @staticmethod
    def subscript_key(node: cst.Subscript) -> cst.BaseExpression | None:
        slice_node = node.slice
        if isinstance(slice_node, cst.Index):
            return slice_node.value
        if not isinstance(slice_node, tuple) or len(slice_node) != 1:
            return None
        element = slice_node[0]
        if not isinstance(element, cst.SubscriptElement):
            return None
        index = element.slice
        if not isinstance(index, cst.Index):
            return None
        return index.value

    @staticmethod
    def build_get_call(parts: DefaultGetParts) -> cst.Call:
        return cst.Call(
            func=cst.Attribute(value=parts.mapping, attr=cst.Name("get")),
            args=[
                cst.Arg(value=parts.key),
                cst.Arg(value=parts.default),
            ],
        )
