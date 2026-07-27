"""Native rule for ``hoist-statement-from-if``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule
from refactor.rules.native.stmt_helpers import hoist_duplicate_trailing_stmt

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class HoistStatementFromIfRule(IfRewriteRule):
    rule_id = "hoist-statement-from-if"
    summary = "Hoist statement from if"
    message = "Hoist a shared trailing statement out of both branches"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        return hoist_duplicate_trailing_stmt(node)
