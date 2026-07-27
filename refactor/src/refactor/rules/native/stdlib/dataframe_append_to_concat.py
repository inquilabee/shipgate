"""Native rule for ``dataframe-append-to-concat``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class DataframeAppendToConcatRule(PatternNativeRule):
    rule_id = "dataframe-append-to-concat"
    kind_value = "suggestion"
    summary = "Dataframe append to concat"
    needle = "dataframe_append_to_concat"
    replacement = "Review pandas pattern for dataframe-append-to-concat"
