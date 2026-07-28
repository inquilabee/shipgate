"""Script/module gate argv and environment construction."""

from __future__ import annotations

import shutil
import sys
from typing import TYPE_CHECKING

from shipgate.gates.config import (
    gate_env_from_config,
    load_gate_config,
    write_resolved_gate_config,
)
from shipgate.gates.ignore import ignore_env
from shipgate.gates.paths import gates_lib_path, resolve_gate_script
from shipgate.gates.scope_paths import gate_scope_paths

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.domain.project import ProjectConfig


def is_gate_tool(tool: ToolDefinition) -> bool:
    return tool.script is not None or tool.module is not None


def prepare_gate_execution(
    resolved: ResolvedRequest,
    *,
    project: ProjectConfig | None = None,
) -> tuple[tuple[str, ...], dict[str, str]]:
    target = str(resolved.options.paths[0]) if resolved.options.paths else "."

    env = dict(resolved.environment.env)
    env |= {
        "SHIPGATE_ROOT": str(resolved.project_root),
        "SHIPGATE_TARGET": target,
        "SHIPGATE_CHECK_ID": resolved.tool.id,
        "SHIPGATE_PYTHON": sys.executable,
        "SHIPGATE_REPORT": str(resolved.output_path),
    }

    precomputed_path = resolved.options.extra.get("gate_config_path")
    precomputed_env = resolved.options.extra.get("gate_env")
    if isinstance(precomputed_path, str) and isinstance(precomputed_env, dict):
        env["SHIPGATE_GATE_CONFIG"] = precomputed_path
        env |= {str(k): str(v) for k, v in precomputed_env.items()}
    else:
        config = load_gate_config(
            resolved.tool,
            resolved.project_root,
            project,
            config_paths=tuple(resolved.options.config),
        )
        resolved_config = write_resolved_gate_config(
            resolved.tool.id,
            resolved.project_root,
            config,
        )
        env["SHIPGATE_GATE_CONFIG"] = str(resolved_config)
        env |= gate_env_from_config(config, resolved.project_root)

    env |= ignore_env(resolved.project_root, extra_patterns=resolved.options.exclude)
    if scope_paths := gate_scope_paths(resolved):
        env["SHIPGATE_SCOPE_PATHS"] = "\n".join(scope_paths)

    if resolved.tool.module:
        return (
            module_gate_argv(resolved, config_path=env["SHIPGATE_GATE_CONFIG"]),
            env,
        )

    env["SHIPGATE_GATES_LIB"] = str(gates_lib_path())
    script_path = resolve_gate_script(resolved.tool, resolved.project_root)
    bash = shutil.which("bash") or "/bin/bash"
    return (bash, str(script_path)), env


def module_gate_argv(resolved: ResolvedRequest, *, config_path: str) -> tuple[str, ...]:
    module = resolved.tool.module
    if not module:
        raise RuntimeError(f"tool {resolved.tool.id!r} has no module")
    return (
        sys.executable,
        "-m",
        module,
        "--root",
        str(resolved.project_root),
        "--config",
        config_path,
        "--report",
        str(resolved.output_path),
    )
