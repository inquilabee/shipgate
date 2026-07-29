"""Native rule for ``return-or-yield-outside-function``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    code_for_expr,
    code_for_small_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class ReturnOrYieldOutsideFunctionRule:
    rule_id = "return-or-yield-outside-function"
    summary = "Return or yield outside function"
    apply_mode = ApplyMode.HINT
    message = "Remove return or yield outside a function"
    kind = RuleKind.REFACTOR

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, ReturnYieldFinder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)


class ReturnYieldFinder(HitCollector):
    def __init__(self, *, path: str) -> None:
        super().__init__(path=path)
        self.function_depth = 0

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        _ = node
        self.function_depth += 1
        return True

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
    ) -> None:
        _ = original_node
        self.function_depth -= 1

    def visit_Return(self, node: cst.Return) -> bool:
        if self.function_depth == 0:
            self.hits.append(
                make_hit(
                    rule_id=ReturnOrYieldOutsideFunctionRule.rule_id,
                    message=ReturnOrYieldOutsideFunctionRule.message,
                    path=self.path,
                    before=code_for_small_stmt(node),
                    after="",
                ),
            )
        return True

    def visit_Yield(self, node: cst.Yield) -> bool:
        if self.function_depth == 0:
            self.hits.append(
                make_hit(
                    rule_id=ReturnOrYieldOutsideFunctionRule.rule_id,
                    message=ReturnOrYieldOutsideFunctionRule.message,
                    path=self.path,
                    before=code_for_expr(node),
                    after="",
                ),
            )
        return True
