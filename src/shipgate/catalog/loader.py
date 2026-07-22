"""Bundled catalog loader."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from shipgate.catalog.validate import validate_catalog
from shipgate.domain.catalog import (
    Catalog,
    CliOptionDefinition,
    ConfigurationDefinition,
    InstallDefinition,
    SuiteDefinition,
    ToolDefinition,
    WorkflowDefinition,
    WorkflowStep,
)
from shipgate.domain.modes import RunMode
from shipgate.errors import CatalogError


def load_catalog(path: Path | None = None) -> Catalog:
    if path is None:
        bundled = resources.files("shipgate.catalog.bundled")
        catalog_path = bundled / "catalog.yaml"
        raw_text = catalog_path.read_text(encoding="utf-8")
        bundled_root = Path(str(bundled))
    else:
        raw_text = path.read_text(encoding="utf-8")
        bundled_root = path.parent
    try:
        raw = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise CatalogError(f"invalid catalog YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise CatalogError("catalog must be a mapping")
    catalog = _parse_catalog(raw)
    validate_catalog(catalog, bundled_root)
    return catalog


def _parse_catalog(raw: dict) -> Catalog:
    tools_raw = raw.get("tools", {}) or {}
    suites_raw = raw.get("suites", {}) or {}
    workflows_raw = raw.get("workflows", {}) or {}
    capabilities_raw = raw.get("capabilities", {}) or {}
    tools = {tid: _parse_tool(tid, tdata) for tid, tdata in tools_raw.items()}
    suites = {sid: _parse_suite(sid, sdata) for sid, sdata in suites_raw.items()}
    workflows = {wid: _parse_workflow(wid, wdata) for wid, wdata in workflows_raw.items()}
    capabilities = {
        str(name): tuple(str(tool_id) for tool_id in (members or []))
        for name, members in capabilities_raw.items()
    }
    return Catalog(tools=tools, suites=suites, workflows=workflows, capabilities=capabilities)


def _parse_tool(tool_id: str, raw: dict) -> ToolDefinition:
    cli = {
        name: CliOptionDefinition(
            flag=opt.get("flag"),
            style=opt.get("style", "scalar"),
            separator=opt.get("separator", ","),
            position=opt.get("position"),
            required=bool(opt.get("required", False)),
            default=opt.get("default"),
            aggregate=opt.get("aggregate"),
        )
        for name, opt in (raw.get("cli") or {}).items()
    }
    config_raw = raw.get("configuration") or {}
    configuration = ConfigurationDefinition(
        bundled=config_raw.get("bundled"),
        discover=tuple(config_raw.get("discover", []) or []),
        pyproject_section=config_raw.get("pyproject_section"),
        precedence=tuple(config_raw.get("precedence", ["cli", "repo", "bundled"])),
        merge=bool(config_raw.get("merge", False)),
    )
    install_raw = raw.get("install")
    install = None
    if install_raw:
        install = InstallDefinition(
            manager=install_raw["manager"],
            package=install_raw["package"],
            version=install_raw.get("version", ""),
            binary=install_raw.get("binary"),
        )
    modes = tuple(RunMode(m) for m in raw.get("modes", ["check"]))
    option_order = tuple(raw.get("option_order", list(cli.keys())))
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
    )


def _parse_suite(suite_id: str, raw: dict) -> SuiteDefinition:
    return SuiteDefinition(
        id=suite_id,
        members=tuple(raw.get("members", []) or []),
        parallel=bool(raw.get("parallel", False)),
        fail_fast=bool(raw.get("fail_fast", raw.get("fail-fast", False))),
    )


def _parse_workflow(workflow_id: str, raw: list) -> WorkflowDefinition:
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
