"""Bundled catalog loader."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from shipgate.catalog.validate import validate_catalog
from shipgate.core.yaml_io import load_yaml_mapping
from shipgate.domain.catalog import (
    Catalog,
    CliOptionDefinition,
    ConfigurationDefinition,
    InstallDefinition,
    ScopeCriteria,
    SuiteDefinition,
    ToolDefinition,
    WorkflowDefinition,
    WorkflowStep,
)
from shipgate.domain.modes import RunMode
from shipgate.errors import CatalogError
from shipgate.paths import project_catalog_dir


def load_catalog(path: Path | None = None, *, project_root: Path | None = None) -> Catalog:
    if path is None:
        bundled = resources.files("shipgate.catalog.bundled")
        bundled_root = Path(str(bundled))
        raw = load_bundled_catalog_raw(bundled)
        if project_root is not None:
            project_raw = load_project_catalog_raw(project_root)
            if project_raw:
                raw = merge_catalog_raw(raw, project_raw)
    else:
        raw = load_yaml_mapping(
            path, error_cls=CatalogError, invalid_message="invalid catalog YAML"
        )
        bundled_root = path.parent
    if not isinstance(raw, dict):
        raise CatalogError("catalog must be a mapping")
    catalog = parse_catalog(raw)
    validate_catalog(catalog, bundled_root)
    return catalog


def merge_catalog_raw(base: dict, overlay: dict) -> dict:
    """Merge project catalog overlay onto bundled raw catalog data."""
    merged = dict(base)
    for section in ("tools", "suites", "workflows", "capabilities"):
        overlay_section = overlay.get(section)
        if not overlay_section:
            continue
        base_section = dict(merged.get(section, {}))
        base_section.update(overlay_section)
        merged[section] = base_section
    return merged


def load_project_catalog_raw(project_root: Path) -> dict | None:
    """Load raw catalog data from `.shipgate/catalog/` when present."""
    catalog_dir = project_catalog_dir(project_root)
    if not catalog_dir.is_dir():
        return None
    raw: dict = {}
    tools_dir = catalog_dir / "tools"
    if tools_dir.is_dir():
        raw["tools"] = load_bundled_tools(tools_dir)
    for section in ("suites", "workflows", "capabilities"):
        section_path = catalog_dir / f"{section}.yaml"
        if section_path.is_file():
            raw[section] = load_catalog_section(catalog_dir, section)
    return raw or None


def load_bundled_catalog_raw(bundled: object) -> dict:
    """Load split catalog from bundled/catalog/ directory."""
    bundled_root = Path(str(bundled))
    catalog_dir = bundled_root / "catalog"
    raw: dict = {"tools": load_bundled_tools(catalog_dir / "tools")}
    for section in ("suites", "workflows", "capabilities"):
        raw[section] = load_catalog_section(catalog_dir, section)
    return raw


def load_bundled_tools(tools_dir: Path) -> dict:
    tools: dict = {}
    for tool_path in sorted(tools_dir.iterdir()):
        if tool_path.suffix != ".yaml":
            continue
        tool_id, tool_data = parse_tool_file(tool_path)
        tools[tool_id] = tool_data
    return tools


def parse_tool_file(tool_path: Path) -> tuple[str, dict]:
    tool_raw = load_yaml_mapping(
        tool_path,
        error_cls=CatalogError,
        invalid_message=f"invalid catalog YAML: {tool_path.name}",
    )
    if not isinstance(tool_raw, dict):
        raise CatalogError(f"tool file must be a mapping: {tool_path.name}")
    expected_id = tool_path.stem
    if len(tool_raw) != 1 or expected_id not in tool_raw:
        raise CatalogError(
            f"tool file {tool_path.name!r} must contain exactly one key {expected_id!r}"
        )
    return expected_id, tool_raw[expected_id]


def load_catalog_section(catalog_dir: Path, section: str) -> dict:
    section_path = catalog_dir / f"{section}.yaml"
    section_raw = load_yaml_mapping(
        section_path,
        error_cls=CatalogError,
        invalid_message=f"invalid catalog YAML: {section_path.name}",
    )
    if not isinstance(section_raw, dict) or section not in section_raw:
        raise CatalogError(f"expected top-level {section!r} key in {section_path.name}")
    return section_raw[section]


def parse_catalog(raw: dict) -> Catalog:
    tools_raw = raw.get("tools", {}) or {}
    suites_raw = raw.get("suites", {}) or {}
    workflows_raw = raw.get("workflows", {}) or {}
    capabilities_raw = raw.get("capabilities", {}) or {}
    return Catalog(
        tools=parse_tools(tools_raw),
        suites=parse_suites(suites_raw),
        workflows=parse_workflows(workflows_raw),
        capabilities=parse_capabilities(capabilities_raw),
    )


def parse_tools(raw: dict) -> dict[str, ToolDefinition]:
    return {tid: parse_tool(tid, tdata) for tid, tdata in raw.items()}


def parse_suites(raw: dict) -> dict[str, SuiteDefinition]:
    return {sid: parse_suite(sid, sdata) for sid, sdata in raw.items()}


def parse_workflows(raw: dict) -> dict[str, WorkflowDefinition]:
    return {wid: parse_workflow(wid, wdata) for wid, wdata in raw.items()}


def parse_capabilities(raw: dict) -> dict[str, tuple[str, ...]]:
    return {
        str(name): tuple(str(tool_id) for tool_id in (members or []))
        for name, members in raw.items()
    }


def parse_tool(tool_id: str, raw: dict) -> ToolDefinition:
    cli = parse_cli_options(raw.get("cli") or {})
    configuration = parse_configuration(raw.get("configuration") or {})
    install = parse_install(raw.get("install"))
    modes = tuple(RunMode(m) for m in raw.get("modes", ["check"]))
    option_order = tuple(raw.get("option_order", list(cli.keys())))
    scope = parse_scope(raw.get("scope") or {})
    return ToolDefinition(
        id=tool_id,
        executable=raw.get("executable", tool_id),
        script=raw.get("script"),
        subcommand=tuple(raw.get("subcommand", []) or []),
        cli=cli,
        configuration=configuration,
        capabilities=tuple(raw.get("capabilities", []) or []),
        install=install,
        normalizer=raw.get("normalizer", "generic_exit"),
        modes=modes,
        option_order=option_order,
        scope=scope,
    )


def parse_cli_options(raw: dict) -> dict[str, CliOptionDefinition]:
    return {
        name: CliOptionDefinition(
            flag=opt.get("flag"),
            style=opt.get("style", "scalar"),
            separator=opt.get("separator", ","),
            position=opt.get("position"),
            required=bool(opt.get("required", False)),
            default=opt.get("default"),
            aggregate=opt.get("aggregate"),
        )
        for name, opt in raw.items()
    }


def parse_configuration(raw: dict) -> ConfigurationDefinition:
    return ConfigurationDefinition(
        bundled=raw.get("bundled"),
        discover=tuple(raw.get("discover", []) or []),
        pyproject_section=raw.get("pyproject_section"),
        precedence=tuple(raw.get("precedence", ["cli", "repo", "bundled"])),
        merge=bool(raw.get("merge", False)),
    )


def parse_install(raw: dict | None) -> InstallDefinition | None:
    if not raw:
        return None
    return InstallDefinition(
        manager=raw["manager"],
        package=raw["package"],
        version=raw.get("version", ""),
        binary=raw.get("binary"),
        requires=tuple(raw.get("requires", []) or []),
    )


def parse_scope(raw: dict) -> ScopeCriteria:
    extensions = tuple(normalize_extension(ext) for ext in raw.get("extensions", []) or [])
    globs = tuple(str(item) for item in raw.get("globs", []) or [])
    delivery = str(raw.get("delivery", "root"))
    return ScopeCriteria(extensions=extensions, globs=globs, delivery=delivery)


def normalize_extension(value: object) -> str:
    text = str(value).strip()
    if not text:
        return text
    return text if text.startswith(".") else f".{text}"


def parse_suite(suite_id: str, raw: dict) -> SuiteDefinition:
    return SuiteDefinition(
        id=suite_id,
        members=tuple(raw.get("members", []) or []),
        parallel=bool(raw.get("parallel", False)),
        fail_fast=bool(raw.get("fail_fast", raw.get("fail-fast", False))),
    )


def parse_workflow(workflow_id: str, raw: list) -> WorkflowDefinition:
    if not isinstance(raw, list):
        raise CatalogError(f"workflow {workflow_id!r} must be a list of steps")
    steps: list[WorkflowStep] = []
    for index, step_raw in enumerate(raw):
        if not isinstance(step_raw, dict) or len(step_raw) != 1:
            raise CatalogError(
                f"workflow {workflow_id!r} step {index} must be a single-mode mapping"
            )
        mode_name, members_raw = next(iter(step_raw.items()))
        try:
            mode = RunMode(mode_name)
        except ValueError as exc:
            raise CatalogError(
                f"workflow {workflow_id!r} step {index} has invalid mode {mode_name!r}"
            ) from exc
        if not isinstance(members_raw, list):
            raise CatalogError(f"workflow {workflow_id!r} step {index} members must be a list")
        steps.append(
            WorkflowStep(
                mode=mode,
                members=tuple(str(member) for member in members_raw),
            )
        )
    if not steps:
        raise CatalogError(f"workflow {workflow_id!r} has no steps")
    return WorkflowDefinition(id=workflow_id, steps=tuple(steps))
