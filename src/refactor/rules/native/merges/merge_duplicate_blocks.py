"""Native rule for ``merge-duplicate-blocks``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule, duplicated_if_body

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


class MergeDuplicateBlocksRule(IfRewriteRule):
    rule_id = "merge-duplicate-blocks"
    summary = "Merge duplicate blocks"
    message = "Merge duplicate if and else blocks"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> Sequence[BodyStatement] | None:
        body = duplicated_if_body(node)
        if body is None:
            return None
        return [cast("BodyStatement", stmt) for stmt in body]
