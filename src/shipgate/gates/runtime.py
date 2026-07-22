"""Script gate argv and environment construction."""

from __future__ import annotations

import shutil
import sys
from typing import TYPE_CHECKING

from shipgate.gates.config import gate_env_from_config, load_gate_config, write_resolved_gate_config
from shipgate.gates.ignore import ignore_env
from shipgate.gates.paths import gates_lib_path, resolve_gate_script

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.domain.project import ProjectConfig


def is_gate_tool(tool) -> bool:
    return "Gates" in tool.capabilities


def prepare_gate_execution(
    resolved: ResolvedRequest,
    *,
    project: ProjectConfig | None = None,
) -> tuple[tuple[str, ...], dict[str, str]]:
    script_path = resolve_gate_script(resolved.tool, resolved.project_root)
    bash = shutil.which("bash") or "/bin/bash"
    argv = (bash, str(script_path))

    target = "."
    if resolved.options.paths:
        target = str(resolved.options.paths[0])

    env = dict(resolved.environment.env)
    env.update(
        {
            "SHIPGATE_ROOT": str(resolved.project_root),
            "SHIPGATE_TARGET": target,
            "SHIPGATE_CHECK_ID": resolved.tool.id,
            "SHIPGATE_PYTHON": sys.executable,
            "SHIPGATE_REPORT": str(resolved.output_path),
            "SHIPGATE_GATES_LIB": str(gates_lib_path()),
        }
    )

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
    env.update(gate_env_from_config(config, resolved.project_root))
    env.update(ignore_env(resolved.project_root, extra_patterns=resolved.options.exclude))
    return argv, env
