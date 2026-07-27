"""Native rule for ``hoist-similar-statement-from-if``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule, hoist_duplicate_trailing_stmt

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class HoistSimilarStatementFromIfRule(IfRewriteRule):
    rule_id = "hoist-similar-statement-from-if"
    summary = "Hoist similar statement from if"
    message = "Hoist identical trailing statements from if branches"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        return hoist_duplicate_trailing_stmt(node)
