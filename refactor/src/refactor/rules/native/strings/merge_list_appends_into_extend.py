"""Native rule for ``merge-list-appends-into-extend``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule, list_appends_to_extend

if TYPE_CHECKING:
    from collections.abc import Sequence


class MergeListAppendsIntoExtendRule(BodySequenceRewriteRule):
    rule_id = "merge-list-appends-into-extend"
    summary = "Merge list appends into extend"
    message = "Merge adjacent list appends into extend"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        return list_appends_to_extend(body)
