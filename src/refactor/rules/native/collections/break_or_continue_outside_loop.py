"""Native rule for ``break-or-continue-outside-loop``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    code_for_small_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class BreakOrContinueOutsideLoopRule:
    rule_id = "break-or-continue-outside-loop"
    summary = "Break or continue outside loop"
    message = "Remove break or continue outside a loop"
    kind = RuleKind.REFACTOR
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, BreakContinueFinder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)


class BreakContinueFinder(HitCollector):
    def __init__(self, *, path: str) -> None:
        super().__init__(path=path)
        self.loop_depth = 0

    def _enter_loop(self) -> None:
        self.loop_depth += 1

    def _leave_loop(self) -> None:
        self.loop_depth -= 1

    def visit_For(self, node: cst.For) -> bool:  # ruff:ignore[invalid-function-name]
        _ = node
        self._enter_loop()
        return True

    def leave_For(self, original_node: cst.For) -> None:  # ruff:ignore[invalid-function-name]
        _ = original_node
        self._leave_loop()

    def visit_While(self, node: cst.While) -> bool:  # ruff:ignore[invalid-function-name]
        _ = node
        self._enter_loop()
        return True

    def leave_While(self, original_node: cst.While) -> None:  # ruff:ignore[invalid-function-name]
        _ = original_node
        self._leave_loop()

    def visit_Break(self, node: cst.Break) -> bool:  # ruff:ignore[invalid-function-name]
        self._record_outside_loop(node)
        return True

    def visit_Continue(self, node: cst.Continue) -> bool:  # ruff:ignore[invalid-function-name]
        self._record_outside_loop(node)
        return True

    def _record_outside_loop(self, node: cst.BaseSmallStatement) -> None:
        if self.loop_depth != 0:
            return
        self.hits.append(
            make_hit(
                rule_id=BreakOrContinueOutsideLoopRule.rule_id,
                message=BreakOrContinueOutsideLoopRule.message,
                path=self.path,
                before=code_for_small_stmt(node),
                after="",
            ),
        )
