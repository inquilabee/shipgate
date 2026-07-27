"""Native rule for ``lift-duplicated-conditional``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule, hoist_duplicate_trailing_stmt

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class LiftDuplicatedConditionalRule(IfRewriteRule):
    rule_id = "lift-duplicated-conditional"
    summary = "Lift duplicated conditional"
    message = "Lift duplicate trailing conditional work out of branches"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        return hoist_duplicate_trailing_stmt(node)
