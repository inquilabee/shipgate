"""Stub refactor rules used in runner tests."""

from __future__ import annotations

from typing import cast

from refactor.protocol import ApplyMode, Hit, Location, RefactorRule, RuleKind
from refactor.runner import apply_auto_rule


class StillDetectingRule:
    rule_id = "still-detecting-stub"
    kind = RuleKind.REFACTOR
    summary = "Stub rule whose apply still leaves detectable hits"
    apply_mode = ApplyMode.AUTO

    def detect(self, source: str, path: str) -> list[Hit]:
        return (
            []
            if "HIT_MARKER" not in source
            else [
                Hit(
                    rule_id=self.rule_id,
                    message="marker present",
                    location=Location(path=path, line=1, column=1),
                )
            ]
        )

    def apply(self, source: str, hits: list[Hit]) -> str | None:
        _ = self, hits
        return source.replace("HIT_MARKER", "STILL_HAS_HIT_MARKER")


def apply_still_detecting_rule(source: str, path) -> str:
    rule = cast("RefactorRule", StillDetectingRule())
    return apply_auto_rule(rule, source, path)
