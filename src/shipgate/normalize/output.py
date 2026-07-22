"""Shared helpers for reading tool stdout and output files."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from shipgate.domain.reports import CheckReport, Finding
from shipgate.errors import NormalizationError

if TYPE_CHECKING:
    from collections.abc import Callable

    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


def looks_like_json(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("{") or stripped.startswith("[")


def read_tool_output(request: ResolvedRequest, result: ProcessResult) -> str:
    stdout = result.stdout
    output_path = request.options.output or request.output_path
    if (
        output_path is not None
        and output_path.is_file()
        and (not stdout.strip() or not looks_like_json(stdout))
    ):
        return output_path.read_text(encoding="utf-8")
    return stdout


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


def normalize_json_items(
    request: ResolvedRequest,
    result: ProcessResult,
    *,
    items_key: str | None,
    item_to_finding: Callable[[dict[str, Any], str], Finding],
    invalid_message: str,
    decode_error: str | None = None,
    allow_empty_on_success: bool = False,
) -> CheckReport:
    check_id = request.tool.id
    stdout = read_tool_output(request, result)
    if result.exit_code == 0 and not stdout.strip():
        return empty_pass_report(check_id)
    payload = decode_json_payload(
        stdout,
        check_id=check_id,
        result=result,
        items_key=items_key,
        decode_error=decode_error,
        allow_empty_on_success=allow_empty_on_success,
    )
    if isinstance(payload, CheckReport):
        return payload
    items = extract_items(payload, items_key=items_key, invalid_message=invalid_message)
    findings = tuple(item_to_finding(item, check_id) for item in items)
    return findings_report(check_id, result, findings)


def extract_items(
    payload: object,
    *,
    items_key: str | None,
    invalid_message: str,
) -> list[dict[str, Any]]:
    if items_key is None:
        if not isinstance(payload, list):
            raise NormalizationError(invalid_message)
        return cast(
            "list[dict[str, Any]]",
            [item for item in payload if isinstance(item, dict)],
        )
    if not isinstance(payload, dict):
        raise NormalizationError(invalid_message)
    items = payload.get(items_key, [])
    if not isinstance(items, list):
        raise NormalizationError(invalid_message)
    return cast(
        "list[dict[str, Any]]",
        [item for item in items if isinstance(item, dict)],
    )
