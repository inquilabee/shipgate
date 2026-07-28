"""Replace ``for x in ys: yield x`` with ``yield from ys``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    BodyStatement,
    IndentedBlockCollector,
    apply_with_transformer,
    check_single_for_named_action,
    code_for_stmt,
    detect_with_visitor,
    make_hit,
    match_named_for,
    single_small_stmt,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class YieldFromRule:
    rule_id = "yield-from"
    kind = RuleKind.REFACTOR
    summary = "Replace `for x in ys: yield x` with `yield from ys`"
    safe_apply = True

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, YieldFromRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, YieldFromRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_IndentedBlock(  # ruff:ignore[invalid-function-name]
            self,
            original_node: cst.IndentedBlock,
            updated_node: cst.IndentedBlock,
        ) -> cst.IndentedBlock:
            _ = self, original_node
            transformed = YieldFromRule.transform_body(updated_node.body)
            return (
                updated_node if transformed is None else updated_node.with_changes(body=transformed)
            )

    class Finder(IndentedBlockCollector):
        def __init__(self, *, path: str) -> None:
            super().__init__(path=path, checker=YieldFromRule.check_body)

    @staticmethod
    def check_body(
        body: Sequence[cst.BaseStatement],
        hits: list[Hit],
        path: str,
    ) -> None:
        check_single_for_named_action(
            body,
            hits,
            path,
            action_name=YieldFromRule.yielded_name,
            build_hit=YieldFromRule.hit_for,
        )

    @staticmethod
    def yielded_name(body: cst.IndentedBlock) -> str | None:
        small = single_small_stmt(body)
        if not isinstance(small, cst.Expr) or not isinstance(small.value, cst.Yield):
            return None
        if small.value.value is None or not isinstance(small.value.value, cst.Name):
            return None
        return small.value.value.value

    @staticmethod
    def transform_body(
        body: Sequence[cst.BaseStatement],
    ) -> list[BodyStatement] | None:
        if len(body) != 1:
            return None
        match = match_named_for(body[0])
        if match is None:
            return None
        for_stmt, iterable = match
        if not isinstance(for_stmt.target, cst.Name):
            return None
        if not isinstance(for_stmt.body, cst.IndentedBlock):
            return None
        matched_name = YieldFromRule.yielded_name(for_stmt.body)
        if matched_name is None or matched_name != for_stmt.target.value:
            return None
        yield_from = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.Yield(value=cst.From(item=iterable)))]
        )
        return [yield_from]

    @staticmethod
    def hit_for(for_stmt: cst.For, iterable: cst.BaseExpression, path: str) -> Hit:
        yield_from = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.Yield(value=cst.From(item=iterable)))]
        )
        return make_hit(
            rule_id="yield-from",
            message="Prefer `yield from` over yield-in-loop",
            path=path,
            before=code_for_stmt(for_stmt),
            after=code_for_stmt(yield_from),
        )
