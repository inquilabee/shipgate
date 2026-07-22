"""Gitleaks JSON normalizer."""

from __future__ import annotations

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.normalize.core.json import JsonItemsNormalizer


class GitleaksNormalizer(JsonItemsNormalizer):
    items_key = None
    invalid_message = "gitleaks output must be a JSON array"
    decode_error = "invalid gitleaks JSON output"

    def item_to_finding(self, item: dict, check_id: str) -> Finding:
        location = None
        file_path = item.get("File") or item.get("file")
        if file_path:
            location = FindingLocation(
                path=str(file_path),
                line=item.get("StartLine") or item.get("startLine"),
                column=item.get("StartColumn") or item.get("startColumn"),
            )
        return Finding(
            check_id=check_id,
            rule_id=str(item.get("RuleID") or item.get("ruleID") or "GITLEAKS"),
            severity="error",
            message=str(item.get("Description") or item.get("description") or "secret detected"),
            location=location,
            extra={"raw": dict(item)},
        )
