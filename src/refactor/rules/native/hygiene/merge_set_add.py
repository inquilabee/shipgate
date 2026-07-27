"""Native rule for ``merge-set-add``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule, set_adds_to_update

if TYPE_CHECKING:
    from collections.abc import Sequence


class MergeSetAddRule(BodySequenceRewriteRule):
    rule_id = "merge-set-add"
    summary = "Merge set add"
    message = "Merge adjacent set adds into update"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        return set_adds_to_update(body)
