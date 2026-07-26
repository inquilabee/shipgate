"""Radon distribution metrics and absolute threshold findings."""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING, ClassVar

from shipgate.domain.reports import Finding
from shipgate.paths import (
    RADON_CC_AVG_CACHE_KEY,
    RADON_CC_MAX_CACHE_KEY,
    RADON_CC_MEDIAN_CACHE_KEY,
    RADON_CC_P95_CACHE_KEY,
    RADON_MI_AVG_CACHE_KEY,
    RADON_MI_MEDIAN_CACHE_KEY,
    RADON_MI_MIN_CACHE_KEY,
    RADON_MI_P95_CACHE_KEY,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class RadonMetrics:
    """Compute CC/MI summaries and emit absolute metric-gate findings."""

    METRIC_PRECISION: ClassVar[int] = 4

    @classmethod
    def cc_metrics(cls, payload: Mapping[str, object]) -> dict[str, object]:
        return cls.metric_extra(
            cls.cc_complexity_values(payload),
            worse_when="higher",
            extreme_kind="maximum",
            average_cache_key=RADON_CC_AVG_CACHE_KEY,
            median_cache_key=RADON_CC_MEDIAN_CACHE_KEY,
            extreme_cache_key=RADON_CC_MAX_CACHE_KEY,
            p95_cache_key=RADON_CC_P95_CACHE_KEY,
        )

    @classmethod
    def mi_metrics(cls, payload: Mapping[str, object]) -> dict[str, object]:
        return cls.metric_extra(
            cls.mi_values(payload),
            worse_when="lower",
            extreme_kind="minimum",
            average_cache_key=RADON_MI_AVG_CACHE_KEY,
            median_cache_key=RADON_MI_MEDIAN_CACHE_KEY,
            extreme_cache_key=RADON_MI_MIN_CACHE_KEY,
            p95_cache_key=RADON_MI_P95_CACHE_KEY,
        )

    @classmethod
    def metric_extra(
        cls,
        values: list[float],
        *,
        worse_when: str,
        extreme_kind: str,
        average_cache_key: str,
        median_cache_key: str,
        extreme_cache_key: str,
        p95_cache_key: str,
    ) -> dict[str, object]:
        if not values:
            return {}
        average = round(sum(values) / len(values), cls.METRIC_PRECISION)
        median = round(statistics.median(values), cls.METRIC_PRECISION)
        extreme_raw = min(values) if extreme_kind == "minimum" else max(values)
        extreme = round(extreme_raw, cls.METRIC_PRECISION)
        p95 = round(cls.percentile(values, 95.0), cls.METRIC_PRECISION)
        return {
            "metric_average": average,
            "metric_median": median,
            "metric_extreme": extreme,
            "metric_extreme_kind": extreme_kind,
            "metric_p95": p95,
            "metric_count": len(values),
            "metric_worse_when": worse_when,
            "metric_average_cache_key": average_cache_key,
            "metric_median_cache_key": median_cache_key,
            "metric_extreme_cache_key": extreme_cache_key,
            "metric_p95_cache_key": p95_cache_key,
        }

    @staticmethod
    def percentile(values: list[float], pct: float) -> float:
        """Inclusive linear interpolation (Excel PERCENTILE.INC style)."""
        if not values:
            raise ValueError("percentile requires at least one value")
        if len(values) == 1:
            return values[0]
        ordered = sorted(values)
        rank = (pct / 100.0) * (len(ordered) - 1)
        low = int(rank)
        high = min(low + 1, len(ordered) - 1)
        frac = rank - low
        return ordered[low] * (1.0 - frac) + ordered[high] * frac

    @staticmethod
    def cc_complexity_values(payload: Mapping[str, object]) -> list[float]:
        values: list[float] = []
        for blocks in payload.values():
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                complexity = block.get("complexity")
                if isinstance(complexity, (int, float)):
                    values.append(float(complexity))
        return values

    @staticmethod
    def mi_values(payload: Mapping[str, object]) -> list[float]:
        values: list[float] = []
        for item in payload.values():
            if not isinstance(item, dict):
                continue
            mi_value = item.get("mi")
            if isinstance(mi_value, (int, float)):
                values.append(float(mi_value))
        return values

    @classmethod
    def absolute_threshold_findings(
        cls,
        check_id: str,
        metrics: Mapping[str, object],
        options_extra: Mapping[str, object],
        *,
        metric_label: str,
    ) -> list[Finding]:
        findings: list[Finding] = []
        worse_when = metrics.get("metric_worse_when")
        if not isinstance(worse_when, str):
            return findings

        for rule_id, subject, current_key, mode_key, bound_key in (
            (
                "average-threshold",
                f"Average {metric_label}",
                "metric_average",
                "average_mode",
                "average_threshold",
            ),
            (
                "median-threshold",
                f"Median {metric_label}",
                "metric_median",
                "median_mode",
                "median_threshold",
            ),
            (
                "p95-threshold",
                f"P95 {metric_label}",
                "metric_p95",
                "p95_mode",
                "p95_threshold",
            ),
        ):
            finding = cls.bound_finding(
                check_id,
                metrics.get(current_key),
                options_extra.get(bound_key),
                worse_when=worse_when,
                mode=options_extra.get(mode_key),
                rule_id=rule_id,
                subject=subject,
            )
            if finding is not None:
                findings.append(finding)

        extreme = cls.extreme_threshold_finding(
            check_id,
            metrics,
            options_extra,
            worse_when=worse_when,
            metric_label=metric_label,
        )
        if extreme is not None:
            findings.append(extreme)
        return findings

    @classmethod
    def extreme_threshold_finding(
        cls,
        check_id: str,
        metrics: Mapping[str, object],
        options_extra: Mapping[str, object],
        *,
        worse_when: str,
        metric_label: str,
    ) -> Finding | None:
        kind = metrics.get("metric_extreme_kind")
        if kind == "minimum":
            mode_key, bound_key, rule_id, label = (
                "minimum_mode",
                "minimum_threshold",
                "minimum-threshold",
                "Minimum",
            )
        elif kind == "maximum":
            mode_key, bound_key, rule_id, label = (
                "maximum_mode",
                "maximum_threshold",
                "maximum-threshold",
                "Maximum",
            )
        else:
            return None
        return cls.bound_finding(
            check_id,
            metrics.get("metric_extreme"),
            options_extra.get(bound_key),
            worse_when=worse_when,
            mode=options_extra.get(mode_key),
            rule_id=rule_id,
            subject=f"{label} {metric_label}",
        )

    @classmethod
    def bound_finding(
        cls,
        check_id: str,
        current_raw: object,
        bound_raw: object,
        *,
        worse_when: str,
        mode: object,
        rule_id: str,
        subject: str,
    ) -> Finding | None:
        if mode != "threshold":
            return None
        if not isinstance(current_raw, (int, float)) or not isinstance(bound_raw, (int, float)):
            return None
        current = float(current_raw)
        bound = float(bound_raw)
        if worse_when == "higher" and current > bound:
            msg = f"{subject} {current:.4f} exceeds ceiling {bound:g}"
        elif worse_when == "lower" and current < bound:
            msg = f"{subject} {current:.4f} is below floor {bound:g}"
        else:
            return None
        return Finding(
            check_id=check_id,
            rule_id=rule_id,
            severity="error",
            message=msg,
        )
