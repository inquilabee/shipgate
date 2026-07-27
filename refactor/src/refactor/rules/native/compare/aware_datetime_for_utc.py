"""Native rule for ``aware-datetime-for-utc``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class AwareDatetimeForUtcRule(PatternNativeRule):
    rule_id = "aware-datetime-for-utc"
    kind_value = "suggestion"
    summary = "Aware datetime for utc"
    needle = "aware_datetime_for_utc"
    replacement = "Review loop pattern for aware-datetime-for-utc"
