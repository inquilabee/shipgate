"""Catalog YAML dict → domain object parser."""

from __future__ import annotations

from shipgate.domain.catalog import (
    Catalog,
    CliOptionDefinition,
    ConfigurationDefinition,
    InstallDefinition,
    ScopeCriteria,
    SuiteDefinition,
    ToolDefinition,
)
from shipgate.domain.modes import RunMode


class CatalogParser:
    """Transform merged raw catalog YAML dicts into frozen domain objects.

    Maps tools and suites into a ``Catalog`` without I/O or validation.
    """

    def __init__(self, raw: dict) -> None:
        self._raw = raw

    @classmethod
    def parse(cls, raw: dict) -> Catalog:
        return cls(raw)._parse()

    def _parse(self) -> Catalog:
        tools_raw = self._raw.get("tools", {}) or {}
        suites_raw = self._raw.get("suites", {}) or {}
        return Catalog(
            tools=self._parse_tools(tools_raw),
            suites=self._parse_suites(suites_raw),
        )

    def _parse_tools(self, raw: dict) -> dict[str, ToolDefinition]:
        return {tool_id: self._parse_tool(tool_id, tool_data) for tool_id, tool_data in raw.items()}

    def _parse_suites(self, raw: dict) -> dict[str, SuiteDefinition]:
        return {
            suite_id: self._parse_suite(suite_id, suite_data)
            for suite_id, suite_data in raw.items()
        }

    def _parse_tool(self, tool_id: str, raw: dict) -> ToolDefinition:
        cli = self._parse_cli_options(raw.get("cli") or {})
        configuration = self._parse_configuration(raw.get("configuration") or {})
        install = self._parse_install(raw.get("install"))
        modes = tuple(RunMode(mode) for mode in raw.get("modes", ["check"]))
        option_order = tuple(raw.get("option_order", list(cli.keys())))
        scope = self._parse_scope(raw.get("scope") or {})
        return ToolDefinition(
            id=tool_id,
            executable=raw.get("executable", tool_id),
            script=raw.get("script"),
            subcommand=tuple(raw.get("subcommand", []) or []),
            cli=cli,
            configuration=configuration,
            install=install,
            normalizer=raw.get("normalizer", "generic_exit"),
            modes=modes,
            option_order=option_order,
            scope=scope,
        )

    def _parse_cli_options(self, raw: dict) -> dict[str, CliOptionDefinition]:
        return {
            name: CliOptionDefinition(
                flag=option.get("flag"),
                style=option.get("style", "scalar"),
                separator=option.get("separator", ","),
                position=option.get("position"),
                required=bool(option.get("required", False)),
                default=option.get("default"),
                aggregate=option.get("aggregate"),
            )
            for name, option in raw.items()
        }

    def _parse_configuration(self, raw: dict) -> ConfigurationDefinition:
        return ConfigurationDefinition(
            bundled=raw.get("bundled"),
            discover=tuple(raw.get("discover", []) or []),
            pyproject_section=raw.get("pyproject_section"),
            precedence=tuple(raw.get("precedence", ["cli", "repo", "bundled"])),
            merge=bool(raw.get("merge", False)),
        )

    def _parse_install(self, raw: dict | None) -> InstallDefinition | None:
        if not raw:
            return None
        return InstallDefinition(
            manager=raw["manager"],
            package=raw["package"],
            version=raw.get("version", ""),
            binary=raw.get("binary"),
            requires=tuple(raw.get("requires", []) or []),
        )

    def _parse_scope(self, raw: dict) -> ScopeCriteria:
        extensions = tuple(
            self._normalize_extension(extension) for extension in raw.get("extensions", []) or []
        )
        globs = tuple(str(item) for item in raw.get("globs", []) or [])
        delivery = str(raw.get("delivery", "root"))
        return ScopeCriteria(extensions=extensions, globs=globs, delivery=delivery)

    def _normalize_extension(self, value: object) -> str:
        text = str(value).strip()
        if not text:
            return text
        return text if text.startswith(".") else f".{text}"

    def _parse_suite(self, suite_id: str, raw: dict) -> SuiteDefinition:
        return SuiteDefinition(
            id=suite_id,
            members=tuple(raw.get("members", []) or []),
            parallel=bool(raw.get("parallel", False)),
            fail_fast=bool(raw.get("fail_fast", raw.get("fail-fast", False))),
        )
