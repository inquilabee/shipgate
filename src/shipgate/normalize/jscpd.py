"""jscpd JSON normalizer — threshold breaches are code findings, not tool crashes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.normalize.core import BaseNormalizer, empty_pass_report, tool_exit_report

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult

THRESHOLD_MARKER = "too many duplicates"
REPORT_NAME = "jscpd-report.json"


class JscpdNormalizer(BaseNormalizer):
    """Normalize jscpd clones and threshold failures into code findings."""

    DEFAULT_OUTPUT_BY_TOOL: ClassVar[dict[str, str]] = {
        "jscpd.check.python": ".shipgate/reports/jscpd-python",
        "jscpd.check.other": ".shipgate/reports/jscpd-other",
    }

    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        report_path = self.resolve_report_path(request, result)
        payload = self.load_report(report_path) if report_path is not None else None

        if result.exit_code == 0:
            return empty_pass_report(check_id)

        if payload is not None:
            findings = self.findings_from_report(check_id, payload, result)
            if findings:
                return CheckReport(
                    check_id=check_id,
                    tool_id=check_id,
                    status="failed",
                    exit_code=result.exit_code,
                    findings=tuple(findings),
                )

        if self.is_threshold_failure(result):
            return CheckReport(
                check_id=check_id,
                tool_id=check_id,
                status="failed",
                exit_code=result.exit_code,
                findings=(self.threshold_finding(check_id, result),),
            )

        return tool_exit_report(check_id, result)

    def resolve_report_path(self, request: ResolvedRequest, result: ProcessResult) -> Path | None:
        root = request.project_root
        candidates: list[Path] = []
        for config_path in request.options.config:
            output_dir = self.output_dir_from_config(config_path)
            if output_dir is not None:
                path = output_dir if output_dir.is_absolute() else root / output_dir
                candidates.append(path / REPORT_NAME)
        default_rel = self.DEFAULT_OUTPUT_BY_TOOL.get(request.tool.id)
        if default_rel:
            candidates.append(root / default_rel / REPORT_NAME)
        stream_text = f"{result.stderr}\n{result.stdout}"
        candidates.extend(
            Path(match.group(1)) for match in re.finditer(r"(\S+/jscpd-report\.json)", stream_text)
        )
        for path in candidates:
            if path.is_file():
                return path
        return None

    @staticmethod
    def output_dir_from_config(config_path: Path) -> Path | None:
        if not config_path.is_file():
            return None
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        output = payload.get("output")
        if isinstance(output, str) and output.strip():
            return Path(output.strip())
        return None

    @staticmethod
    def load_report(path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def findings_from_report(
        self,
        check_id: str,
        payload: dict[str, Any],
        result: ProcessResult,
    ) -> list[Finding]:
        findings = [self.clone_finding(check_id, item) for item in self.duplicate_items(payload)]
        findings = [finding for finding in findings if finding is not None]
        if not findings and self.is_threshold_failure(result):
            findings.append(self.threshold_finding(check_id, result, payload=payload))
        elif findings and self.is_threshold_failure(result):
            threshold = self.threshold_finding(check_id, result, payload=payload)
            findings.insert(0, threshold)
        return findings

    @staticmethod
    def duplicate_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw = payload.get("duplicates")
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    @staticmethod
    def clone_finding(check_id: str, item: dict[str, Any]) -> Finding | None:
        first = item.get("firstFile")
        if not isinstance(first, dict):
            return None
        path = first.get("name")
        if not isinstance(path, str) or not path.strip():
            return None
        line = JscpdNormalizer.file_start_line(first)
        other = JscpdNormalizer.second_file_suffix(item.get("secondFile"))
        lines_bit = JscpdNormalizer.duplicate_lines_label(item.get("lines"))
        return Finding(
            check_id=check_id,
            rule_id="duplicate",
            severity="error",
            message=f"Duplicated code: {lines_bit}{other}",
            location=FindingLocation(
                path=path.strip(),
                line=line,
            ),
            extra={"raw": dict(item)},
        )

    @staticmethod
    def file_start_line(file_entry: dict[str, Any]) -> int | None:
        start_loc = file_entry.get("startLoc")
        if isinstance(start_loc, dict):
            line = start_loc.get("line")
            if isinstance(line, int):
                return line
        start = file_entry.get("start")
        return start if isinstance(start, int) else None

    @staticmethod
    def second_file_suffix(second: object) -> str:
        if not isinstance(second, dict):
            return ""
        typed = {str(key): value for key, value in second.items()}
        name = typed.get("name")
        if not isinstance(name, str):
            return ""
        other_line = JscpdNormalizer.file_start_line(typed)
        suffix = f" (also {name}"
        if other_line is not None:
            suffix += f":{other_line}"
        return suffix + ")"

    @staticmethod
    def duplicate_lines_label(lines: object) -> str:
        return f"{lines} lines" if isinstance(lines, int) else "duplicate block"

    def threshold_finding(
        self,
        check_id: str,
        result: ProcessResult,
        *,
        payload: dict[str, Any] | None = None,
    ) -> Finding:
        message = self.threshold_message(result, payload)
        return Finding(
            check_id=check_id,
            rule_id="threshold",
            severity="error",
            message=message,
            location=None,
        )

    def threshold_message(self, result: ProcessResult, payload: dict[str, Any] | None) -> str:
        for stream in (result.stderr, result.stdout):
            for line in stream.splitlines():
                if THRESHOLD_MARKER in line.lower():
                    return re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
        pct = self.total_percentage(payload) if payload else None
        if pct is not None:
            return f"jscpd found too many duplicates ({pct:.1f}%) over configured threshold"
        return result.stderr.strip() or result.stdout.strip() or "Duplication over threshold"

    @staticmethod
    def total_percentage(payload: dict[str, Any] | None) -> float | None:
        if not payload:
            return None
        stats = payload.get("statistics") or payload.get("statistic")
        if not isinstance(stats, dict):
            return None
        total = stats.get("total")
        if not isinstance(total, dict):
            return None
        percentage = total.get("percentage")
        if isinstance(percentage, (int, float)):
            return float(percentage)
        return None

    @staticmethod
    def is_threshold_failure(result: ProcessResult) -> bool:
        text = f"{result.stderr}\n{result.stdout}".lower()
        return THRESHOLD_MARKER in text
