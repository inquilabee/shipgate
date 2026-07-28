"""Replace membership tests on literal lists with literal sets."""

from __future__ import annotations

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


class CollectionIntoSetRule:
    rule_id = "collection-into-set"
    kind = RuleKind.REFACTOR
    summary = "Replace `x in [a, b, c]` with `x in {a, b, c}` for simple literals"
    safe_apply = True

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, CollectionIntoSetRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, CollectionIntoSetRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_Comparison(  # ruff:ignore[invalid-function-name]
            self,
            original_node: cst.Comparison,
            updated_node: cst.Comparison,
        ) -> cst.BaseExpression:
            _ = self, original_node
            replacement = CollectionIntoSetRule.transform_comparison(updated_node)
            return updated_node if replacement is None else replacement

    class Finder(HitCollector):
        def visit_Comparison(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.Comparison,
        ) -> bool:
            for comp in node.comparisons:
                if not isinstance(comp.operator, cst.In):
                    continue
                if not isinstance(comp.comparator, cst.List):
                    continue
                if not CollectionIntoSetRule.is_simple_literal_list(comp.comparator):
                    continue
                self.hits.append(CollectionIntoSetRule.hit_for(node, comp.comparator, self.path))
            return True

    @staticmethod
    def is_simple_literal_list(node: cst.List) -> bool:
        return (
            all(CollectionIntoSetRule.is_simple_literal(element.value) for element in node.elements)
            if node.elements
            else False
        )

    @staticmethod
    def is_simple_literal(node: cst.BaseExpression) -> bool:
        return isinstance(
            node,
            (cst.Integer, cst.Float, cst.Imaginary, cst.SimpleString, cst.Name),
        ) and (not isinstance(node, cst.Name) or node.value in {"True", "False", "None"})

    @staticmethod
    def list_to_set(list_node: cst.List) -> cst.Set:
        set_elements = [
            cst.Element(value=element.value, comma=element.comma) for element in list_node.elements
        ]
        return cst.Set(elements=set_elements)

    @staticmethod
    def transform_comparison(node: cst.Comparison) -> cst.Comparison | None:
        changed = False
        new_comparisons: list[cst.ComparisonTarget] = []
        for comp in node.comparisons:
            if (
                isinstance(comp.operator, cst.In)
                and isinstance(comp.comparator, cst.List)
                and CollectionIntoSetRule.is_simple_literal_list(comp.comparator)
            ):
                set_node = CollectionIntoSetRule.list_to_set(comp.comparator)
                new_comparisons.append(
                    cst.ComparisonTarget(operator=comp.operator, comparator=set_node)
                )
                changed = True
                continue
            new_comparisons.append(comp)
        return cst.Comparison(left=node.left, comparisons=new_comparisons) if changed else None

    @staticmethod
    def hit_for(
        comparison: cst.Comparison,
        list_node: cst.List,
        path: str,
    ) -> Hit:
        set_node = CollectionIntoSetRule.list_to_set(list_node)
        new_comparisons = []
        for comp in comparison.comparisons:
            if comp.comparator is list_node:
                new_comparisons.append(
                    cst.ComparisonTarget(operator=comp.operator, comparator=set_node)
                )
            else:
                new_comparisons.append(comp)
        after_expr = cst.Comparison(left=comparison.left, comparisons=new_comparisons)
        return make_hit(
            rule_id="collection-into-set",
            message="Prefer set literal for membership test",
            path=path,
            before=code_for_expr(comparison),
            after=code_for_expr(after_expr),
        )
