"""Native rule for ``merge-repeated-ifs``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule

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
        for index, left in enumerate(body[:-1]):
            right = body[index + 1]
            if not isinstance(left, cst.If) or not isinstance(right, cst.If):
                continue
            if left.orelse is not None or right.orelse is not None:
                continue
            if not isinstance(left.body, cst.IndentedBlock) or not isinstance(
                right.body,
                cst.IndentedBlock,
            ):
                continue
            if not left.test.deep_equals(right.test):
                continue
            return (
                [left, right],
                [
                    left.with_changes(
                        body=left.body.with_changes(
                            body=[*left.body.body, *right.body.body],
                        ),
                    ),
                ],
            )
        return None
