"""Native rule for ``simplify-single-exception-tuple``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    code_for_expr,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class SimplifySingleExceptionTupleRule:
    rule_id = "simplify-single-exception-tuple"
    kind = RuleKind.REFACTOR
    summary = "Simplify single exception tuple"
    apply_mode = ApplyMode.HINT
    message = "Use the exception type directly instead of a one-item tuple"

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, SimplifySingleExceptionTupleRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_ExceptHandler(
            self,
            node: cst.ExceptHandler,
        ) -> bool:
            exception_type = node.type
            if not isinstance(exception_type, cst.Tuple) or len(exception_type.elements) != 1:
                return True
            replacement = exception_type.elements[0].value
            self.hits.append(
                make_hit(
                    rule_id=SimplifySingleExceptionTupleRule.rule_id,
                    message=SimplifySingleExceptionTupleRule.message,
                    path=self.path,
                    before=code_for_expr(exception_type),
                    after=code_for_expr(replacement),
                ),
            )
            return True
