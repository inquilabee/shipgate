"""Calibrate radon MI/CC metric thresholds from a live distribution."""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from shipgate.core.process import run_command
from shipgate.errors import ConfigError, ExecutionError
from shipgate.normalize.radon_metrics import RadonMetrics
from shipgate.normalize.radon_scores import RadonScores
from shipgate.paths import PROJECT_MANAGED_PYTHON_ENV

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.normalize.radon_scores import ScoredMetric

RadonKind = Literal["mi", "cc"]


def parse_radon_kind(kind: str) -> RadonKind:
    if kind == "mi":
        return "mi"
    if kind == "cc":
        return "cc"
    raise ConfigError(f"radon calibrate kind must be 'mi' or 'cc', got {kind!r}")


@dataclass(frozen=True)
class RadonCalibration:
    """Measured distribution plus suggested absolute thresholds."""

    kind: RadonKind
    count: int
    mean: float
    median: float
    minimum: float
    maximum: float
    p5: float
    p10: float
    p95: float
    offenders: tuple[ScoredMetric, ...]
    suggestions: Mapping[str, float]

    @property
    def worse_when(self) -> str:
        return "lower" if self.kind == "mi" else "higher"

    @property
    def check_id(self) -> str:
        return f"radon.{self.kind}"


class RadonCalibrator:
    """Build calibration reports from radon JSON payloads."""

    PRECISION: int = 4

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        kind: RadonKind,
        top: int = RadonScores.DEFAULT_OFFENDER_LIMIT,
    ) -> RadonCalibration:
        if kind == "mi":
            values = RadonMetrics.mi_values(payload)
            items = RadonScores.mi_items(payload)
            worse_when = "lower"
        else:
            values = RadonMetrics.cc_complexity_values(payload)
            items = RadonScores.cc_items(payload)
            worse_when = "higher"
        if not values:
            raise ConfigError(f"no radon.{kind} scores in payload")
        mean = round(sum(values) / len(values), cls.PRECISION)
        median = round(statistics.median(values), cls.PRECISION)
        minimum = round(min(values), cls.PRECISION)
        maximum = round(max(values), cls.PRECISION)
        p5 = round(RadonMetrics.percentile(values, 5.0), cls.PRECISION)
        p10 = round(RadonMetrics.percentile(values, 10.0), cls.PRECISION)
        p95 = round(RadonMetrics.percentile(values, 95.0), cls.PRECISION)
        offenders = tuple(RadonScores.ranked_offenders(items, worse_when=worse_when, limit=top))
        suggestions = cls.suggest_thresholds(
            kind=kind,
            median=median,
            minimum=minimum,
            maximum=maximum,
            p5=p5,
            p10=p10,
            p95=p95,
        )
        return RadonCalibration(
            kind=kind,
            count=len(values),
            mean=mean,
            median=median,
            minimum=minimum,
            maximum=maximum,
            p5=p5,
            p10=p10,
            p95=p95,
            offenders=offenders,
            suggestions=suggestions,
        )

    @classmethod
    def suggest_thresholds(
        cls,
        *,
        kind: RadonKind,
        median: float,
        minimum: float,
        maximum: float,
        p5: float,
        p10: float,
        p95: float,
    ) -> dict[str, float]:
        """Suggest passable absolute bounds (floors for MI, ceilings for CC)."""
        if kind == "mi":
            return {
                "median": cls.suggest_floor(median),
                "minimum": cls.suggest_floor(minimum),
                "p5": cls.suggest_floor(p5),
                "p10": cls.suggest_floor(p10),
                "p95": cls.suggest_floor(p95),
            }
        return {
            "median": cls.suggest_ceiling(median),
            "maximum": cls.suggest_ceiling(maximum),
            "p5": cls.suggest_ceiling(p5),
            "p10": cls.suggest_ceiling(p10),
            "p95": cls.suggest_ceiling(p95),
        }

    @staticmethod
    def suggest_floor(value: float) -> float:
        return math.floor(value * 10.0) / 10.0

    @staticmethod
    def suggest_ceiling(value: float) -> float:
        return math.ceil(value * 10.0) / 10.0


class RadonCalibrationRenderer:
    """Format calibration as human text or YAML binding snippets."""

    @classmethod
    def render(cls, calibration: RadonCalibration, *, yaml_snippet: bool = False) -> str:
        if yaml_snippet:
            return cls.yaml_snippet(calibration)
        return cls.text_report(calibration)

    @classmethod
    def text_report(cls, calibration: RadonCalibration) -> str:
        lines = [
            f"{calibration.check_id} calibration (n={calibration.count})",
            (
                f"  mean={calibration.mean:.4f} median={calibration.median:.4f} "
                f"min={calibration.minimum:.4f} max={calibration.maximum:.4f}"
            ),
            (f"  p5={calibration.p5:.4f} p10={calibration.p10:.4f} p95={calibration.p95:.4f}"),
            "  suggested thresholds:",
        ]
        for key in ("median", "p5", "p10", "p95", "minimum", "maximum"):
            if key not in calibration.suggestions:
                continue
            lines.append(f"    {key}: {calibration.suggestions[key]:g}")
        if calibration.offenders:
            label = "lowest" if calibration.kind == "mi" else "highest"
            lines.append(f"  {label} {len(calibration.offenders)}:")
            for item in calibration.offenders:
                detail = f" ({item.detail})" if item.detail else ""
                lines.append(f"    {item.score:7.2f} {item.path}{detail}")
        lines.append("")
        lines.append(cls.yaml_snippet(calibration).rstrip())
        lines.append("")
        return "\n".join(lines)

    @classmethod
    def yaml_snippet(cls, calibration: RadonCalibration) -> str:
        suggestions = calibration.suggestions
        lines = [
            "checks:",
            f"  {calibration.check_id}:",
            "    threshold: B",
        ]
        for field in ("median", "p5", "p10", "p95"):
            if field not in suggestions:
                continue
            lines.append(f"    {field}-mode: threshold")
            lines.append(f"    {field}-threshold: {suggestions[field]:g}")
        extreme = "minimum" if calibration.kind == "mi" else "maximum"
        if extreme in suggestions:
            lines.append(f"    {extreme}-mode: threshold")
            lines.append(f"    {extreme}-threshold: {suggestions[extreme]:g}")
        lines.append("")
        return "\n".join(lines)


class RadonCalibrationRunner:
    """Load JSON or invoke managed/system radon for calibration."""

    @classmethod
    def calibrate(
        cls,
        project_root: Path,
        *,
        kind: RadonKind,
        paths: Sequence[Path],
        json_path: Path | None = None,
        top: int = RadonScores.DEFAULT_OFFENDER_LIMIT,
    ) -> RadonCalibration:
        payload = cls.load_payload(
            project_root,
            kind=kind,
            paths=paths,
            json_path=json_path,
        )
        return RadonCalibrator.from_payload(payload, kind=kind, top=top)

    @classmethod
    def load_payload(
        cls,
        project_root: Path,
        *,
        kind: RadonKind,
        paths: Sequence[Path],
        json_path: Path | None,
    ) -> dict[str, object]:
        if json_path is not None:
            return cls.read_json_file(json_path)
        return cls.run_radon(project_root, kind=kind, paths=paths)

    @staticmethod
    def read_json_file(path: Path) -> dict[str, object]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"invalid radon JSON file: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigError("radon JSON must be an object")
        return raw

    @classmethod
    def run_radon(
        cls,
        project_root: Path,
        *,
        kind: RadonKind,
        paths: Sequence[Path],
    ) -> dict[str, object]:
        radon_bin = cls.resolve_radon(project_root)
        targets = [str(path) for path in paths] or ["."]
        argv = [radon_bin, kind, "-s", "-j", *targets]
        completed = run_command(argv, cwd=project_root)
        if completed.returncode not in {0, 1}:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise ExecutionError(
                f"radon {kind} failed (exit {completed.returncode}): {detail}",
            )
        try:
            raw = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise ExecutionError(f"invalid radon JSON output: {exc}") from exc
        if not isinstance(raw, dict):
            raise ExecutionError("radon output must be a JSON object")
        return raw

    @staticmethod
    def resolve_radon(project_root: Path) -> str:
        managed = project_root / PROJECT_MANAGED_PYTHON_ENV / "bin" / "radon"
        if managed.is_file():
            return str(managed)
        return "radon"


def calibrate_radon(
    project_root: Path,
    *,
    kind: str,
    paths: Sequence[Path] | None = None,
    json_path: Path | None = None,
    top: int = RadonScores.DEFAULT_OFFENDER_LIMIT,
    yaml_snippet: bool = False,
) -> str:
    parsed = parse_radon_kind(kind)
    calibration = RadonCalibrationRunner.calibrate(
        project_root,
        kind=parsed,
        paths=tuple(paths or ()),
        json_path=json_path,
        top=top,
    )
    return RadonCalibrationRenderer.render(calibration, yaml_snippet=yaml_snippet)
