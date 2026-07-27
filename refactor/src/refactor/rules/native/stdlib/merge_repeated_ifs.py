"""Native rule for ``merge-repeated-ifs``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import (
    BodySequenceRewriteRule,
    merge_adjacent_ifs_with_same_test,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class MergeRepeatedIfsRule(BodySequenceRewriteRule):
    rule_id = "merge-repeated-ifs"
    summary = "Merge repeated ifs"
    message = "Merge adjacent if statements with identical tests"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        return merge_adjacent_ifs_with_same_test(body)
