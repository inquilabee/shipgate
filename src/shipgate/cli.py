"""ShipGate CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.app import InstallCommand, RunCommand, ShipGateApp
from shipgate.errors import ShipGateError
from shipgate.paths import find_project_root
from shipgate.runtime.project_python import persist_project_python

if TYPE_CHECKING:
    from collections.abc import Callable


def shared_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--config", type=Path, help="Path to shipgate.yaml")
    shared.add_argument("--suite", help="Suite to run")
    shared.add_argument("--check", help="Single check to run")
    shared.add_argument("--target", type=Path, help="Target path")
    shared.add_argument("--error-format", dest="error_format", help="Error output format")
    shared.add_argument("--extra-arg", action="append", default=[], dest="extra_args")
    shared.add_argument("--verbose", action="store_true")
    shared.add_argument("--quiet", action="store_true")
    shared.add_argument(
        "--display-cli",
        action="store_true",
        help="Print each tool subprocess command to stderr before execution",
    )
    shared.add_argument("--ci", action="store_true")
    shared.add_argument("--no-cache", action="store_true")
    shared.add_argument("--changed-only", action="store_true")
    shared.add_argument("--since", help="Git ref for incremental checks")
    shared.add_argument(
        "--project-env",
        type=Path,
        help="Project Python environment path; saved to .shipgate/cache/.env",
    )
    return shared


def build_parser() -> argparse.ArgumentParser:
    shared = shared_parser()
    parser = argparse.ArgumentParser(prog="shipgate", description="Quality gate orchestrator")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", parents=[shared], help="Install tools for selected suite")
    sub.add_parser(
        "update",
        parents=[shared],
        help="Reinstall suite tools to catalog version pins",
    )
    init_parser = sub.add_parser("init", help="Scaffold ShipGate project policy and layout")
    init_sub = init_parser.add_subparsers(dest="init_mode")
    init_sub.add_parser("yaml", help="Create .shipgate/shipgate.yaml (default)")
    init_sub.add_parser("pyproject", help="Merge [tool.shipgate] into pyproject.toml")
    init_parser.add_argument(
        "--configs-only",
        action="store_true",
        help="Scaffold .shipgate/configs without creating policy",
    )
    init_parser.add_argument(
        "--project-env",
        type=Path,
        help="Project Python environment path; saved to .shipgate/cache/.env",
    )

    configs_parser = sub.add_parser("configs", help="Project tool config management")
    configs_sub = configs_parser.add_subparsers(dest="configs_cmd", required=True)
    configs_sub.add_parser("sync", help="Copy missing configs from bundled templates")
    configs_diff = configs_sub.add_parser("diff", help="Diff project configs vs bundled templates")
    configs_diff.add_argument("tool", nargs="?", help="Optional tool id to diff")
    configs_list = configs_sub.add_parser("list", help="Show resolved config path per tool")
    configs_list.add_argument("--suite", help="Suite to list (default: project suite)")
    sub.add_parser("format", parents=[shared], help="Run apply-capable checks")
    sub.add_parser("check", parents=[shared], help="Run report-only checks")

    list_parser = sub.add_parser("list", help="List catalog metadata")
    list_sub = list_parser.add_subparsers(dest="list_target", required=True)
    list_sub.add_parser("suites")
    list_tools = list_sub.add_parser("tools")
    list_tools.add_argument("--tag", help="Filter tools by catalog tag")
    list_sub.add_parser("checks")

    sub.add_parser("schema", help="Print canonical report JSON schema")
    serve_parser = sub.add_parser("serve", help="Start report frontend")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--open", action="store_true", help="Open browser")
    sub.add_parser("lock", help="Write install lockfile")

    baseline_parser = sub.add_parser("baseline", parents=[shared], help="Baseline management")
    baseline_sub = baseline_parser.add_subparsers(dest="baseline_cmd", required=True)
    baseline_sub.add_parser("update", parents=[shared])
    baseline_sub.add_parser("show")

    batch_parser = sub.add_parser("batch", help="Run batch file")
    batch_parser.add_argument("batch_file", type=Path)

    gates_parser = sub.add_parser("gates", help="Local gates")
    gates_sub = gates_parser.add_subparsers(dest="gates_cmd", required=True)
    gates_init = gates_sub.add_parser("init")
    gates_init.add_argument("name", nargs="?", default="gate")
    gates_sub.add_parser("lib-path", help="Print path to bundled gate lib.sh")

    return parser


TOP_LEVEL_COMMANDS = frozenset(
    {
        "install",
        "update",
        "init",
        "configs",
        "format",
        "check",
        "list",
        "schema",
        "serve",
        "lock",
        "baseline",
        "batch",
        "gates",
    }
)


def normalize_argv(argv: list[str] | None, parser: argparse.ArgumentParser) -> argparse.Namespace:
    if (
        argv is not None
        and argv
        and not argv[0].startswith("-")
        and argv[0] not in TOP_LEVEL_COMMANDS
    ):
        argv = ["check", *argv]
    args = parser.parse_args(argv)
    if args.command is None:
        args = parser.parse_args(["check", *(argv or [])])
    return args


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = normalize_argv(argv, parser)
    project_root = find_project_root()
    app = ShipGateApp()
    verbose = getattr(args, "verbose", False)

    try:
        return dispatch_command(app, args, parser, project_root)
    except ShipGateError as exc:
        sys.stderr.write(exc.format() + "\n")
        if verbose:
            raise
        return exc.exit_code
    except Exception as exc:
        sys.stderr.write(f"shipgate: internal error: {exc}\n")
        if verbose:
            raise
        return 4


def dispatch_command(
    app: ShipGateApp,
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    project_root: Path,
) -> int:
    command = args.command or "check"
    project_env = getattr(args, "project_env", None)
    if project_env is not None and command != "init":
        persist_project_python(project_root, project_env)
    handlers: dict[str, Callable[[], int]] = {
        "install": lambda: app.install(
            InstallCommand(
                project_root=project_root,
                config_path=args.config,
                suite=args.suite,
            )
        ),
        "update": lambda: app.update(
            InstallCommand(
                project_root=project_root,
                config_path=args.config,
                suite=args.suite,
            )
        ),
        "init": lambda: dispatch_init(app, args, project_root),
        "configs": lambda: dispatch_configs(app, args, project_root),
        "check": lambda: app.check(run_command(args, project_root)),
        "format": lambda: app.format(run_command(args, project_root)),
        "list": lambda: dispatch_list(app, args, project_root),
        "schema": lambda: write_schema(app),
        "serve": lambda: app.serve(
            project_root,
            host=args.host,
            port=args.port,
            open_browser=getattr(args, "open", False),
        ),
        "lock": lambda: app.lock(project_root),
        "baseline": lambda: dispatch_baseline(app, args, project_root),
        "batch": lambda: app.run_batch(project_root, args.batch_file),
        "gates": lambda: dispatch_gates(app, args, project_root),
    }
    handler = handlers.get(command)
    if handler is not None:
        return handler()
    parser.print_help()
    return 0


def dispatch_init(app: ShipGateApp, args: argparse.Namespace, project_root: Path) -> int:
    mode = getattr(args, "init_mode", None) or "yaml"
    project_env = getattr(args, "project_env", None)
    sys.stdout.write(
        app.init(
            project_root,
            configs_only=getattr(args, "configs_only", False),
            mode=mode,
            project_env=project_env,
        )
    )
    return 0


def dispatch_configs(app: ShipGateApp, args: argparse.Namespace, project_root: Path) -> int:
    if args.configs_cmd == "sync":
        sys.stdout.write(app.configs_sync(project_root))
        return 0
    if args.configs_cmd == "diff":
        sys.stdout.write(app.configs_diff(project_root, getattr(args, "tool", None)))
        return 0
    if args.configs_cmd == "list":
        sys.stdout.write(app.configs_list(project_root, suite=getattr(args, "suite", None)))
        return 0
    return 0


def write_schema(app: ShipGateApp) -> int:
    sys.stdout.write(app.schema())
    return 0


def dispatch_gates(app: ShipGateApp, args: argparse.Namespace, project_root: Path) -> int:
    if args.gates_cmd == "init":
        sys.stdout.write(app.gates_init(project_root, args.name))
        return 0
    if args.gates_cmd == "lib-path":
        sys.stdout.write(app.gates_lib_path())
        return 0
    return 0


def dispatch_list(app: ShipGateApp, args: argparse.Namespace, project_root: Path) -> int:
    if args.list_target == "suites":
        if not getattr(args, "quiet", False) or getattr(args, "verbose", False):
            sys.stdout.write(app.list_suites())
        return 0
    if args.list_target in ("tools", "checks"):
        if not getattr(args, "quiet", False) or getattr(args, "verbose", False):
            if args.list_target == "checks":
                sys.stdout.write(app.list_checks(project_root))
            else:
                sys.stdout.write(app.list_tools(tag=getattr(args, "tag", None)))
        return 0
    return 0


def dispatch_baseline(app: ShipGateApp, args: argparse.Namespace, project_root: Path) -> int:
    if args.baseline_cmd == "update":
        return app.baseline_update(run_command(args, project_root))
    if args.baseline_cmd == "show":
        sys.stdout.write(app.baseline_show(project_root))
        return 0
    return 0


def run_command(args: argparse.Namespace, project_root: Path) -> RunCommand:
    return RunCommand(
        project_root=project_root,
        config_path=getattr(args, "config", None),
        suite=getattr(args, "suite", None),
        check=getattr(args, "check", None),
        target=getattr(args, "target", None),
        error_format=getattr(args, "error_format", None),
        extra_args=tuple(getattr(args, "extra_args", []) or []),
        verbose=getattr(args, "verbose", False),
        quiet=getattr(args, "quiet", False),
        display_cli=getattr(args, "display_cli", False),
        ci=getattr(args, "ci", False),
        no_cache=getattr(args, "no_cache", False),
        changed_only=getattr(args, "changed_only", False),
        since=getattr(args, "since", None),
    )
