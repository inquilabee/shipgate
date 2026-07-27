"""Replace ``for x in ys: yield x`` with ``yield from ys``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    IndentedBlockCollector,
    check_single_for_named_action,
    code_for_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
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
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, YieldFromRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

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
