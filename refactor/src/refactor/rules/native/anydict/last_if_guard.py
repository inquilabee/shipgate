"""Native rule for ``last-if-guard``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence


class LastIfGuardRule(BodySequenceRewriteRule):
    rule_id = "last-if-guard"
    summary = "Last if guard"
    message = "Use a guard clause before the final fallback statement"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        _ = cls, body
        return None
