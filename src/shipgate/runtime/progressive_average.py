"""Progressive metric compare against `.shipgate/cache/.env` baselines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding
from shipgate.paths import PROJECT_CACHE_ENV, parse_env_file, update_project_cache_env

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from shipgate.domain.execution import ResolvedRequest


@dataclass(frozen=True)
class ProgressiveMetricSpec:
    label: str
    current: float
    cache_key: str
    worse_when: str
    rule_id: str


class ProgressiveMetricGate:
    """Compare report metrics to last-saved baselines; persist on non-regression."""

    @classmethod
    def apply(cls, request: ResolvedRequest, report: CheckReport) -> CheckReport:
        specs = cls.metric_specs(request.options.extra, report.extra)
        if not specs:
            return report

        findings: list[Finding] = []
        updates: dict[str, str] = {}
        for spec in specs:
            past = cls.read_baseline(request.project_root, spec.cache_key)
            if past is None:
                past = spec.current
            if cls.is_worse(spec.current, past, worse_when=spec.worse_when):
                findings.append(
                    Finding(
                        check_id=report.check_id,
                        rule_id=spec.rule_id,
                        severity="error",
                        message=(
                            f"{spec.label} metric {spec.current:.4f} is worse than "
                            f"baseline {past:.4f}"
                        ),
                    )
                )
                continue
            updates[spec.cache_key] = cls.format_value(spec.current)

        if updates:
            update_project_cache_env(request.project_root, updates)
        if not findings:
            return report
        return CheckReport(
            check_id=report.check_id,
            tool_id=report.tool_id,
            status="failed",
            exit_code=report.exit_code,
            findings=(*report.findings, *findings),
            stdout_path=report.stdout_path,
            stderr_path=report.stderr_path,
            extra=report.extra,
        )

    @classmethod
    def metric_specs(
        cls,
        options_extra: Mapping[str, object],
        report_extra: Mapping[str, object],
    ) -> list[ProgressiveMetricSpec]:
        worse_when = report_extra.get("metric_worse_when")
        if worse_when not in {"higher", "lower"}:
            return []
        worse = str(worse_when)
        candidates = (
            cls.summary_spec(
                options_extra,
                report_extra,
                worse_when=worse,
                mode_key="average_mode",
                current_key="metric_average",
                cache_key_field="metric_average_cache_key",
                label="Average",
                rule_id="average-progressive",
            ),
            cls.summary_spec(
                options_extra,
                report_extra,
                worse_when=worse,
                mode_key="median_mode",
                current_key="metric_median",
                cache_key_field="metric_median_cache_key",
                label="Median",
                rule_id="median-progressive",
            ),
            cls.summary_spec(
                options_extra,
                report_extra,
                worse_when=worse,
                mode_key="p95_mode",
                current_key="metric_p95",
                cache_key_field="metric_p95_cache_key",
                label="P95",
                rule_id="p95-progressive",
            ),
            cls.extreme_spec(options_extra, report_extra, worse_when=worse),
        )
        return [spec for spec in candidates if spec is not None]

    @staticmethod
    def summary_spec(
        options_extra: Mapping[str, object],
        report_extra: Mapping[str, object],
        *,
        worse_when: str,
        mode_key: str,
        current_key: str,
        cache_key_field: str,
        label: str,
        rule_id: str,
    ) -> ProgressiveMetricSpec | None:
        if options_extra.get(mode_key) != "progressive":
            return None
        current = report_extra.get(current_key)
        cache_key = report_extra.get(cache_key_field)
        if not isinstance(current, (int, float)):
            return None
        if not isinstance(cache_key, str) or not cache_key:
            return None
        return ProgressiveMetricSpec(
            label=label,
            current=float(current),
            cache_key=cache_key,
            worse_when=worse_when,
            rule_id=rule_id,
        )

    @staticmethod
    def extreme_spec(
        options_extra: Mapping[str, object],
        report_extra: Mapping[str, object],
        *,
        worse_when: str,
    ) -> ProgressiveMetricSpec | None:
        kind = report_extra.get("metric_extreme_kind")
        current = report_extra.get("metric_extreme")
        cache_key = report_extra.get("metric_extreme_cache_key")
        if not isinstance(current, (int, float)):
            return None
        if not isinstance(cache_key, str) or not cache_key:
            return None
        if kind == "minimum" and options_extra.get("minimum_mode") == "progressive":
            label = "Minimum"
            rule_id = "minimum-progressive"
        elif kind == "maximum" and options_extra.get("maximum_mode") == "progressive":
            label = "Maximum"
            rule_id = "maximum-progressive"
        else:
            return None
        return ProgressiveMetricSpec(
            label=label,
            current=float(current),
            cache_key=cache_key,
            worse_when=worse_when,
            rule_id=rule_id,
        )

    @staticmethod
    def read_baseline(project_root: Path, cache_key: str) -> float | None:
        env_path = project_root / PROJECT_CACHE_ENV
        if not env_path.is_file():
            return None
        raw = parse_env_file(env_path).get(cache_key)
        if raw is None or raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    @staticmethod
    def is_worse(current: float, past: float, *, worse_when: str) -> bool:
        if worse_when == "higher":
            return current > past
        return current < past

    @staticmethod
    def format_value(value: float) -> str:
        return f"{value:.4f}"


def apply_progressive_average(request: ResolvedRequest, report: CheckReport) -> CheckReport:
    return ProgressiveMetricGate.apply(request, report)
