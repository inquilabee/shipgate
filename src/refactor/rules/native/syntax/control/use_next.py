"""Replace a lone first-element ``for`` loop with ``next(iter(...))``."""

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
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class UseNextRule:
    rule_id = "use-next"
    kind = RuleKind.REFACTOR
    summary = "Replace `for x in xs: return x` with `next(iter(xs))`"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, UseNextRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(IndentedBlockCollector):
        def __init__(self, *, path: str) -> None:
            super().__init__(path=path, checker=UseNextRule.check_body)

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
            action_name=UseNextRule.returned_name,
            build_hit=UseNextRule.hit_for,
        )

    @staticmethod
    def returned_name(body: cst.IndentedBlock) -> str | None:
        small = single_small_stmt(body)
        if not isinstance(small, cst.Return) or small.value is None:
            return None
        if not isinstance(small.value, cst.Name):
            return None
        return small.value.value

    @staticmethod
    def hit_for(for_stmt: cst.For, iterable: cst.BaseExpression, path: str) -> Hit:
        next_call = cst.Call(
            func=cst.Name("next"),
            args=[cst.Arg(value=cst.Call(func=cst.Name("iter"), args=[cst.Arg(value=iterable)]))],
        )
        after_stmt = cst.SimpleStatementLine(body=[cst.Return(value=next_call)])
        return make_hit(
            rule_id="use-next",
            message="Prefer `next(iter(...))` for first element",
            path=path,
            before=code_for_stmt(for_stmt),
            after=code_for_stmt(after_stmt),
        )
