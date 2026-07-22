"""Append findings to script-gate JSON reports."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path


def append_finding(
    report_path: Path,
    rule_id: str,
    severity: str,
    message: str,
    file: str = "",
    line: str = "",
) -> None:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    finding: dict[str, object] = {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
    }
    if file:
        location: dict[str, object] = {"file": file}
        if line:
            with contextlib.suppress(ValueError):
                location["line"] = int(line)
        finding["location"] = location
    payload.setdefault("findings", []).append(finding)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
