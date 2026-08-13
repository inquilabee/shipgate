"""Shared helpers for reading tool stdout and building reports."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding
from shipgate.errors import NormalizationError

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


def looks_like_json(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith(("{", "["))


def read_tool_output(request: ResolvedRequest, result: ProcessResult) -> str:
    stdout = result.stdout
    output_path = request.options.output or request.output_path
    wrote_this_run = output_path is not None and output_path in result.output_files
    return (
        output_path.read_text(encoding="utf-8")
        if (
            wrote_this_run
            and output_path.is_file()
            and (not stdout.strip() or not looks_like_json(stdout))
        )
        else stdout
    )


def tool_exit_report(check_id: str, result: ProcessResult) -> CheckReport:
    message = result.stderr.strip() or result.stdout.strip() or "Tool failed"
    return CheckReport(
        check_id=check_id,
        tool_id=check_id,
        status="failed",
        exit_code=result.exit_code,
        findings=(
            Finding(
                check_id=check_id,
                rule_id="TOOL_EXIT",
                severity="error",
                message=message,
            ),
        ),
    )


def empty_pass_report(check_id: str) -> CheckReport:
    return CheckReport(
        check_id=check_id,
        tool_id=check_id,
        status="passed",
        exit_code=0,
    )


def findings_report(
    check_id: str,
    result: ProcessResult,
    findings: tuple[Finding, ...],
) -> CheckReport:
    status = "failed" if findings or result.exit_code != 0 else "passed"
    return CheckReport(
        check_id=check_id,
        tool_id=check_id,
        status=status,
        exit_code=result.exit_code,
        findings=findings,
    )


def decode_json_payload(
    stdout: str,
    *,
    check_id: str,
    result: ProcessResult,
    items_key: str | None,
    decode_error: str | None,
    allow_empty_on_success: bool,
) -> object | CheckReport:
    try:
        return json.loads(stdout) if stdout.strip() else ([] if items_key is None else {})
    except json.JSONDecodeError as exc:
        if allow_empty_on_success and result.exit_code == 0:
            return empty_pass_report(check_id)
        if decode_error:
            raise NormalizationError(decode_error) from exc
        return tool_exit_report(check_id, result)


def dict_items_from_list(raw: object) -> list[dict[str, object]]:
    return (
        [{str(key): value for key, value in item.items()} for item in raw if isinstance(item, dict)]
        if isinstance(raw, list)
        else []
    )


def extract_items(
    payload: object,
    *,
    items_key: str | None,
    invalid_message: str,
) -> list[dict[str, object]]:
    if items_key is None:
        if not isinstance(payload, list):
            raise NormalizationError(invalid_message)
        return dict_items_from_list(payload)
    if not isinstance(payload, dict):
        raise NormalizationError(invalid_message)
    items = payload.get(items_key, [])
    if not isinstance(items, list):
        raise NormalizationError(invalid_message)
    return dict_items_from_list(items)
