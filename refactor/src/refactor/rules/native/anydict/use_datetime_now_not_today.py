"""Native rule for ``use-datetime-now-not-today``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseDatetimeNowNotTodayRule(PatternNativeRule):
    rule_id = "use-datetime-now-not-today"
    kind_value = "refactor"
    summary = "Use datetime now not today"
    needle = "use_datetime_now_not_today"
    replacement = "Review Sourcery pattern for use-datetime-now-not-today"
