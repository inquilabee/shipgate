"""Append findings to script-gate JSON reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from shipgate.core.json_io import dumps_indented
from shipgate.gates.core.report import gate_finding_payload


def append_finding(
    report_path: Path,
    rule_id: str,
    severity: str,
    message: str,
    file: str = "",
    line: str = "",
) -> None:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload.setdefault("findings", []).append(
        gate_finding_payload(
            rule_id=rule_id,
            severity=severity,
            message=message,
            file=file,
            line=line or None,
        )
    )
    report_path.write_text(dumps_indented(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 4:
        print(
            "usage: append_finding REPORT RULE_ID SEVERITY MESSAGE [FILE] [LINE]",
            file=sys.stderr,
        )
        return 2
    report_path, rule_id, severity, message = args[0], args[1], args[2], args[3]
    file = args[4] if len(args) > 4 else ""
    line = args[5] if len(args) > 5 else ""
    append_finding(Path(report_path), rule_id, severity, message, file, line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
