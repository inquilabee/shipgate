"""Native rule for ``merge-list-append``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import (
    BodySequenceRewriteRule,
    list_appends_to_extend,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class MergeListAppendRule(BodySequenceRewriteRule):
    rule_id = "merge-list-append"
    summary = "Merge list append"
    message = "Merge adjacent list appends into extend"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        return list_appends_to_extend(body)
