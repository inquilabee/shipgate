"""Suggest ``enumerate`` instead of ``range(len(...))`` indexing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    code_for_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class ForIndexReplacementRule:
    rule_id = "for-index-replacement"
    kind = RuleKind.REFACTOR
    summary = "Replace `for i in range(len(xs)): xs[i]` with `enumerate(xs)`"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, ForIndexReplacementRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_For(self, node: cst.For) -> bool:  # ruff:ignore[invalid-function-name]
            match = ForIndexReplacementRule.match_range_len_for(node)
            if match is None:
                return True
            index_name, sequence_name = match
            if not ForIndexReplacementRule.body_uses_subscript(
                node.body, index_name, sequence_name
            ):
                return True
            self.hits.append(
                ForIndexReplacementRule.hit_for(node, index_name, sequence_name, self.path)
            )
            return True

    @staticmethod
    def match_range_len_for(node: cst.For) -> tuple[str, str] | None:
        if node.orelse or not isinstance(node.target, cst.Name):
            return None
        sequence_name = ForIndexReplacementRule.sequence_from_range_len(node.iter)
        if sequence_name is None:
            return None
        return node.target.value, sequence_name

    @staticmethod
    def sequence_from_range_len(iter_expr: cst.BaseExpression) -> str | None:
        if not isinstance(iter_expr, cst.Call):
            return None
        if not isinstance(iter_expr.func, cst.Name) or iter_expr.func.value != "range":
            return None
        if len(iter_expr.args) != 1:
            return None
        return ForIndexReplacementRule.sequence_from_len_call(iter_expr.args[0].value)

    @staticmethod
    def sequence_from_len_call(arg: cst.BaseExpression) -> str | None:
        if not isinstance(arg, cst.Call):
            return None
        if not isinstance(arg.func, cst.Name) or arg.func.value != "len":
            return None
        if len(arg.args) != 1:
            return None
        sequence = arg.args[0].value
        if not isinstance(sequence, cst.Name):
            return None
        return sequence.value

    @staticmethod
    def body_uses_subscript(
        body: cst.BaseSuite,
        index_name: str,
        sequence_name: str,
    ) -> bool:
        return (
            any(
                ForIndexReplacementRule.statement_uses_subscript(stmt, index_name, sequence_name)
                for stmt in body.body
            )
            if isinstance(body, cst.IndentedBlock)
            else False
        )

    @staticmethod
    def statement_uses_subscript(
        stmt: cst.BaseStatement,
        index_name: str,
        sequence_name: str,
    ) -> bool:
        finder = ForIndexReplacementRule.SubscriptFinder(index_name, sequence_name)
        stmt.visit(finder)
        return finder.found

    @staticmethod
    def hit_for(
        for_stmt: cst.For,
        index_name: str,
        sequence_name: str,
        path: str,
    ) -> Hit:
        enumerate_call = cst.Call(
            func=cst.Name("enumerate"),
            args=[cst.Arg(value=cst.Name(sequence_name))],
        )
        after_for = cst.For(
            target=cst.Tuple(
                elements=[
                    cst.Element(value=cst.Name(index_name)),
                    cst.Element(value=cst.Name("_item")),
                ]
            ),
            iter=enumerate_call,
            body=for_stmt.body,
        )
        return make_hit(
            rule_id="for-index-replacement",
            message="Prefer `enumerate()` over `range(len(...))` indexing",
            path=path,
            before=code_for_stmt(for_stmt),
            after=code_for_stmt(after_for),
            suggestion_message=f"Use `for {index_name}, item in enumerate({sequence_name}):`",
        )

    class SubscriptFinder(cst.CSTVisitor):
        def __init__(self, index_name: str, sequence_name: str) -> None:
            self.index_name = index_name
            self.sequence_name = sequence_name
            self.found = False

        def visit_Subscript(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.Subscript,
        ) -> bool:
            if self.found:
                return False
            if not isinstance(node.value, cst.Name):
                return True
            if node.value.value != self.sequence_name:
                return True
            slice_parts = node.slice
            if not (
                isinstance(slice_parts, tuple)
                and len(slice_parts) == 1
                and isinstance(slice_parts[0], cst.SubscriptElement)
                and isinstance(slice_parts[0].slice, cst.Index)
                and isinstance(slice_parts[0].slice.value, cst.Name)
            ):
                return True
            index_expr = slice_parts[0].slice.value
            if index_expr.value == self.index_name:
                self.found = True
                return False
            return True
