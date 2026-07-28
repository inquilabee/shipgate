"""Invoke Ruff and map JSON diagnostics for bridge rules."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from typing import TypeAlias

from refactor.protocol import Suggestion

JsonObject: TypeAlias = Mapping[str, object]


def ruff_command() -> list[str]:
    ruff = shutil.which("ruff")
    return [ruff] if ruff is not None else [sys.executable, "-m", "ruff"]


def run_ruff(
    args: Sequence[str],
    *,
    stdin_input: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # ruff:ignore[subprocess-without-shell-equals-true]
        [*ruff_command(), *args],
        input=stdin_input,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )


def select_arg(codes: frozenset[str]) -> str:
    return f"--select={','.join(sorted(codes))}"


def as_json_object(value: object) -> JsonObject | None:
    return {str(key): item for key, item in value.items()} if isinstance(value, Mapping) else None


RUFF_CONFIG_FLAG = "--config"


def config_args(extra: Sequence[str] | None) -> tuple[str, ...]:
    """Normalize optional Ruff ``--config`` fragments for ``--isolated`` runs."""
    if not extra:
        return ()
    normalized: list[str] = []
    for item in extra:
        if item.startswith(f"{RUFF_CONFIG_FLAG}="):
            normalized.extend([RUFF_CONFIG_FLAG, item.removeprefix(f"{RUFF_CONFIG_FLAG}=")])
        elif item == RUFF_CONFIG_FLAG:
            continue
        elif item.startswith("--"):
            normalized.append(item)
        else:
            normalized.extend([RUFF_CONFIG_FLAG, item])
    return tuple(normalized)


def run_ruff_check(
    source: str,
    path: str,
    codes: frozenset[str],
    *,
    config: Sequence[str] | None = None,
) -> list[JsonObject]:
    completed = run_ruff(
        (
            "check",
            "--isolated",
            select_arg(codes),
            *config_args(config),
            "--output-format=json",
            f"--stdin-filename={path}",
            "-",
        ),
        stdin_input=source,
    )
    if not completed.stdout.strip():
        return []
    raw = json.loads(completed.stdout)
    if not isinstance(raw, list):
        msg = "ruff JSON output must be a list"
        raise TypeError(msg)
    return [obj for item in raw if (obj := as_json_object(item)) is not None]


def run_ruff_fix(
    source: str,
    path: str,
    codes: frozenset[str],
    *,
    config: Sequence[str] | None = None,
) -> str | None:
    completed = run_ruff(
        (
            "check",
            "--isolated",
            select_arg(codes),
            *config_args(config),
            "--fix",
            "--unsafe-fixes",
            "--quiet",
            f"--stdin-filename={path}",
            "-",
        ),
        stdin_input=source,
    )
    return None if completed.returncode not in {0, 1} else completed.stdout


def location_row_column(location: object) -> tuple[int | None, int | None]:
    if not isinstance(location, Mapping):
        return None, None
    row = location.get("row")
    column = location.get("column")
    return (
        int(row) if isinstance(row, int) else None,
        int(column) if isinstance(column, int) else None,
    )


def offset_at(source: str, location: object) -> int | None:
    row, column = location_row_column(location)
    if row is None or column is None or row < 1 or column < 1:
        return None
    lines = source.splitlines(keepends=True)
    if row > len(lines) + 1:
        return None
    return sum(len(line) for line in lines[: row - 1]) + column - 1


def typed_edits(fix: JsonObject) -> list[JsonObject] | None:
    edits = fix.get("edits")
    if not isinstance(edits, list) or not edits:
        return None
    result = [obj for edit in edits if (obj := as_json_object(edit)) is not None]
    return result or None


def edits_span(
    source: str,
    edits: Sequence[JsonObject],
) -> tuple[int | None, int | None]:
    starts: list[int] = []
    ends: list[int] = []
    for edit in edits:
        start = offset_at(source, edit.get("location"))
        end = offset_at(source, edit.get("end_location"))
        if start is None or end is None:
            return None, None
        starts.append(start)
        ends.append(end)
    return min(starts), max(ends)


def apply_edits(source: str, edits: Sequence[JsonObject]) -> str:
    spans: list[tuple[int, int, str]] = []
    for edit in edits:
        start = offset_at(source, edit.get("location"))
        end = offset_at(source, edit.get("end_location"))
        if start is None or end is None:
            continue
        content = edit.get("content")
        spans.append((start, end, "" if content is None else str(content)))
    result = source
    for start, end, content in sorted(spans, key=lambda item: item[0], reverse=True):
        result = "".join([result[:start], content, result[end:]])
    return result


def suggestion_from_diagnostic(
    source: str,
    diagnostic: JsonObject,
) -> Suggestion | None:
    fix_obj = as_json_object(diagnostic.get("fix"))
    if fix_obj is None:
        return None
    edits = typed_edits(fix_obj)
    if edits is None:
        return None
    start, end = edits_span(source, edits)
    if start is None or end is None or start > end:
        return None
    fixed = apply_edits(source, edits)
    after_end = len(fixed) - (len(source) - end)
    raw_message = fix_obj.get("message") or diagnostic.get("message")
    return Suggestion(
        before=source[start:end],
        after=fixed[start:after_end],
        message=str(raw_message) if raw_message else None,
    )
