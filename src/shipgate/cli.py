"""ShipGate CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shipgate.app import InstallCommand, RunCommand, ShipGateApp
from shipgate.errors import ShipGateError
from shipgate.paths import find_project_root


def _shared_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--config", type=Path, help="Path to shipgate.yaml")
    shared.add_argument("--suite", help="Suite to run")
    shared.add_argument("--check", help="Single check to run")
    shared.add_argument("--target", type=Path, help="Target path")
    shared.add_argument("--error-format", dest="error_format", help="Error output format")
    shared.add_argument("--output-dir", type=Path, help="Output directory")
    shared.add_argument("--extra-arg", action="append", default=[], dest="extra_args")
    shared.add_argument("--verbose", action="store_true")
    shared.add_argument("--quiet", action="store_true")
    shared.add_argument("--ci", action="store_true")
    shared.add_argument("--no-cache", action="store_true")
    shared.add_argument("--changed-only", action="store_true")
    shared.add_argument("--since", help="Git ref for incremental checks")
    return shared


def build_parser() -> argparse.ArgumentParser:
    shared = _shared_parser()
    parser = argparse.ArgumentParser(prog="shipgate", description="Quality gate orchestrator")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", parents=[shared], help="Install tools for selected suite")
    sub.add_parser("format", parents=[shared], help="Run apply-capable checks")
    sub.add_parser("check", parents=[shared], help="Run report-only checks")

    list_parser = sub.add_parser("list", help="List catalog metadata")
    list_sub = list_parser.add_subparsers(dest="list_target", required=True)
    list_sub.add_parser("suites")
    list_sub.add_parser("tools")
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if (
        argv is not None
        and argv
        and not argv[0].startswith("-")
        and argv[0]
        not in {
            "install",
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
    ):
        argv = ["check", *argv]
    args = parser.parse_args(argv)
    command = args.command
    if command is None:
        command = "check"
        args = parser.parse_args(["check", *(argv or [])])
    project_root = find_project_root()
    app = ShipGateApp()
    verbose = getattr(args, "verbose", False)

    try:
        if command == "install":
            return app.install(
                InstallCommand(
                    project_root=project_root,
                    config_path=args.config,
                    suite=args.suite,
                )
            )
        if command == "check":
            return app.check(_run_command(args, project_root))
        if command == "format":
            return app.format(_run_command(args, project_root))
        if command == "list":
            if args.list_target == "suites":
                if not getattr(args, "quiet", False) or getattr(args, "verbose", False):
                    sys.stdout.write(app.list_suites())
                return 0
            if args.list_target in ("tools", "checks"):
                if not getattr(args, "quiet", False) or getattr(args, "verbose", False):
                    sys.stdout.write(app.list_tools())
                return 0
        if command == "schema":
            sys.stdout.write(app.schema())
            return 0
        if command == "serve":
            return app.serve(
                project_root,
                host=args.host,
                port=args.port,
                open_browser=getattr(args, "open", False),
            )
        if command == "lock":
            return app.lock(project_root)
        if command == "baseline":
            if args.baseline_cmd == "update":
                return app.baseline_update(_run_command(args, project_root))
            if args.baseline_cmd == "show":
                sys.stdout.write(app.baseline_show(project_root))
                return 0
        if command == "batch":
            return app.run_batch(project_root, args.batch_file)
        if command == "gates" and args.gates_cmd == "init":
            sys.stdout.write(app.gates_init(project_root, args.name))
            return 0
        parser.print_help()
        return 0
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


def _run_command(args: argparse.Namespace, project_root: Path) -> RunCommand:
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
        ci=getattr(args, "ci", False),
        no_cache=getattr(args, "no_cache", False),
        changed_only=getattr(args, "changed_only", False),
        since=getattr(args, "since", None),
    )
