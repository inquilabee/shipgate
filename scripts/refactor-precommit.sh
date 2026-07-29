#!/usr/bin/env bash
set -euo pipefail

files=()
for path in "$@"; do
	case "${path}" in
	src/* | tests/refactor/*) files+=("${path}") ;;
	esac
done

if ((${#files[@]} == 0)); then
	exit 0
fi

exec env PYTHONPATH=src uv run python -m refactor check --strict "${files[@]}"
