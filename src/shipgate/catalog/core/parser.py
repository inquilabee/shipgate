"""Catalog YAML dict → domain object parser."""

from __future__ import annotations

from shipgate.domain.catalog import (
    BinaryDownloadSpec,
    CacheDefinition,
    Catalog,
    CliOptionDefinition,
    ConfigurationDefinition,
    InstallDefinition,
    RequireIfDefinition,
    ScopeCriteria,
    SuggestIfDefinition,
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
        option_order = tuple(raw.get("option_order", list(cli)))
        scope = self._parse_scope(raw.get("scope") or {})
        tags = tuple(str(tag) for tag in raw.get("tags", []) or [])
        cache = self._parse_cache(raw.get("cache"))
        suggest_if = self._parse_suggest_if(raw.get("suggest_if"))
        require_if = self._parse_require_if(raw.get("require_if"))
        return ToolDefinition(
            id=tool_id,
            executable=raw.get("executable", tool_id),
            script=raw.get("script"),
            module=raw.get("module"),
            subcommand=tuple(raw.get("subcommand", []) or []),
            cli=cli,
            configuration=configuration,
            install=install,
            normalizer=raw.get("normalizer", "generic_exit"),
            modes=modes,
            option_order=option_order,
            scope=scope,
            tags=tags,
            cache=cache,
            suggest_if=suggest_if,
            require_if=require_if,
            display_name=str(raw.get("display_name") or ""),
            description=str(raw.get("description") or ""),
            documentation_url=self.tool_documentation_url(raw),
        )

    @staticmethod
    def tool_documentation_url(raw: dict) -> str | None:
        value = raw.get("documentation_url")
        return str(value) if value else None

    @staticmethod
    def _parse_cli_options(raw: dict) -> dict[str, CliOptionDefinition]:
        return {
            name: CliOptionDefinition(
                flag=option.get("flag"),
                style=option.get("style", "scalar"),
                separator=option.get("separator", ","),
                position=option.get("position"),
                required=option.get("required", False),
                default=option.get("default"),
                aggregate=option.get("aggregate"),
            )
            for name, option in raw.items()
        }

    @staticmethod
    def _parse_configuration(raw: dict) -> ConfigurationDefinition:
        return ConfigurationDefinition(
            bundled=raw.get("bundled"),
            discover=tuple(raw.get("discover", []) or []),
            pyproject_section=raw.get("pyproject_section"),
            precedence=tuple(raw.get("precedence", ["cli", "repo", "bundled"])),
            merge=raw.get("merge", False),
        )

    def _parse_install(self, raw: dict | None) -> InstallDefinition | None:
        return (
            InstallDefinition(
                manager=raw["manager"],
                package=raw["package"],
                version=str(raw.get("version", "") or ""),
                binary=raw.get("binary"),
                requires=tuple(raw.get("requires", []) or []),
                allow_path=raw.get("allow_path", True),
                known_bad=tuple(str(item) for item in raw.get("known_bad", []) or []),
                download=self._parse_download(raw.get("download")),
            )
            if raw
            else None
        )

    @staticmethod
    def _parse_download(raw: dict | None) -> BinaryDownloadSpec | None:
        return (
            BinaryDownloadSpec(
                repo=str(raw["repo"]),
                asset_template=str(raw["asset_template"]),
                binary_name=str(raw.get("binary_name") or raw.get("binary") or ""),
                arch_map={
                    str(key): str(value) for key, value in (raw.get("arch_map") or {}).items()
                },
                os_map={str(key): str(value) for key, value in (raw.get("os_map") or {}).items()},
            )
            if raw
            else None
        )

    @staticmethod
    def _parse_cache(raw: dict | None) -> CacheDefinition | None:
        if not raw:
            return None
        ttl = raw.get("ttl_seconds")
        return CacheDefinition(
            results=raw.get("results", True),
            ttl_seconds=int(ttl) if ttl is not None else None,
        )

    @staticmethod
    def _parse_suggest_if(raw: dict | None) -> SuggestIfDefinition | None:
        return (
            SuggestIfDefinition(
                files_present=tuple(str(item) for item in raw.get("files_present", []) or []),
            )
            if raw
            else None
        )

    @staticmethod
    def _parse_require_if(raw: dict | None) -> RequireIfDefinition | None:
        return (
            RequireIfDefinition(
                files_present=tuple(str(item) for item in raw.get("files_present", []) or []),
            )
            if raw
            else None
        )

    def _parse_scope(self, raw: dict) -> ScopeCriteria:
        extensions = tuple(
            self._normalize_extension(extension) for extension in raw.get("extensions", []) or []
        )
        globs = tuple(str(item) for item in raw.get("globs", []) or [])
        delivery = str(raw.get("delivery", "root"))
        return ScopeCriteria(extensions=extensions, globs=globs, delivery=delivery)

    @staticmethod
    def _normalize_extension(value: object) -> str:
        text = str(value).strip()
        return (text if text.startswith(".") else f".{text}") if text else text

    @staticmethod
    def _parse_suite(suite_id: str, raw: dict) -> SuiteDefinition:
        return SuiteDefinition(
            id=suite_id,
            members=tuple(raw.get("members", []) or []),
            parallel=raw.get("parallel", False),
            fail_fast=raw.get("fail_fast", raw.get("fail-fast", False)),
        )
