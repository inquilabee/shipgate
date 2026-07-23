#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=/dev/null
source "$(shipgate gates lib-path)"

gate_init "gate"

# Example: fail when scan target is missing
if [[ ! -d ${SHIPGATE_TARGET:-.} ]]; then
	gate_fail "missing-target" "Scan target not found: ${SHIPGATE_TARGET:-.}"
fi

gate_finish
