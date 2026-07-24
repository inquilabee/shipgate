"""Path-based gate allowlists with documented reasons per entry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shipgate.policy.core.path_allowlist import PathAllowlist, PathAllowlistEntry

__all__ = ["PathAllowlist", "PathAllowlistEntry"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query a path-based YAML allowlist.")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--contains", required=True)
    args = parser.parse_args(argv)
    if PathAllowlist(args.file).contains(args.contains):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
