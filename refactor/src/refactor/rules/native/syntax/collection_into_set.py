"""Replace membership tests on literal lists with literal sets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class CollectionIntoSetRule:
    rule_id = "collection-into-set"
    kind = RuleKind.REFACTOR
    summary = "Replace `x in [a, b, c]` with `x in {a, b, c}` for simple literals"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = CollectionIntoSetRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

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
        if not node.elements:
            return False
        return all(
            CollectionIntoSetRule.is_simple_literal(element.value) for element in node.elements
        )

    @staticmethod
    def is_simple_literal(node: cst.BaseExpression) -> bool:
        return isinstance(
            node,
            (cst.Integer, cst.Float, cst.Imaginary, cst.SimpleString, cst.Name),
        ) and (not isinstance(node, cst.Name) or node.value in {"True", "False", "None"})

    @staticmethod
    def hit_for(
        comparison: cst.Comparison,
        list_node: cst.List,
        path: str,
    ) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=comparison)])]
        ).code.strip()
        set_elements = [
            cst.Element(value=element.value, comma=element.comma) for element in list_node.elements
        ]
        set_node = cst.Set(elements=set_elements)
        new_comparisons = []
        for comp in comparison.comparisons:
            if comp.comparator is list_node:
                new_comparisons.append(
                    cst.ComparisonTarget(operator=comp.operator, comparator=set_node)
                )
            else:
                new_comparisons.append(comp)
        after_expr = cst.Comparison(left=comparison.left, comparisons=new_comparisons)
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=after_expr)])]
        ).code.strip()
        return Hit(
            rule_id="collection-into-set",
            message="Prefer set literal for membership test",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
