"""pip-audit JSON normalizer."""

from __future__ import annotations

from typing import Any

from shipgate.domain.reports import Finding
from shipgate.normalize.core import JsonItemsNormalizer, finding_location


class PipAuditNormalizer(JsonItemsNormalizer):
    items_key = "dependencies"
    invalid_message = "pip-audit output must be a JSON object"
    allow_empty_on_success = True

    def parse_items(self, payload: object) -> list[dict[str, Any]]:
        dependencies = super().parse_items(payload)
        items: list[dict[str, Any]] = []
        for dependency in dependencies:
            items.extend(self._vulns_for_dependency(dependency))
        return items

    def item_to_finding(self, item: dict[str, Any], check_id: str) -> Finding:
        package = str(item.get("package") or "unknown")
        version = str(item.get("version") or "")
        vuln_id = str(item.get("id") or "VULN")
        version_text = f" {version}" if version else ""
        return Finding(
            check_id=check_id,
            rule_id=vuln_id,
            severity="error",
            message=self._finding_message(item, package, version_text),
            location=finding_location("pyproject.toml"),
            extra={"raw": dict(item)},
        )

    @staticmethod
    def _vulns_for_dependency(dependency: dict[str, Any]) -> list[dict[str, Any]]:
        vulns = dependency.get("vulns") or []
        if not isinstance(vulns, list):
            return []
        return [
            {
                "package": dependency.get("name"),
                "version": dependency.get("version"),
                **vuln,
            }
            for vuln in vulns
            if isinstance(vuln, dict)
        ]

    @staticmethod
    def _finding_message(item: dict[str, Any], package: str, version_text: str) -> str:
        description = str(item.get("description") or "").strip()
        aliases = item.get("aliases") or []
        alias_text = ""
        if isinstance(aliases, list) and aliases:
            alias_text = f" (aliases: {', '.join(str(alias) for alias in aliases)})"
        message = description or f"Known vulnerability in {package}{version_text}"
        return f"{package}{version_text}: {message}{alias_text}"
