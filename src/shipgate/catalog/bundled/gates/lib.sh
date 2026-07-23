#!/usr/bin/env bash
# shipgate script-gate helper library.
# Source from project gates: source "$(shipgate gates lib-path)"
set -euo pipefail

gate_init() {
	GATE_NAME="${1:-script-gate}"
	GATE_FINDING_COUNT=0
	if [[ -z ${SHIPGATE_REPORT:-} ]]; then
		echo "gate_init: SHIPGATE_REPORT is not set (shipgate runner should set this)" >&2
		exit 2
	fi
	mkdir -p "$(dirname "${SHIPGATE_REPORT}")"
	printf '%s\n' '{"findings":[]}' >"${SHIPGATE_REPORT}"
}

_gate_append_finding() {
	local rule_id="$1"
	local severity="$2"
	local message="$3"
	local file="${4:-}"
	local line="${5:-}"
	"${SHIPGATE_PYTHON:-python3}" -m shipgate.gates.append_finding \
		"${SHIPGATE_REPORT}" "${rule_id}" "${severity}" "${message}" "${file}" "${line}"
	GATE_FINDING_COUNT=$((GATE_FINDING_COUNT + 1))
}

gate_fail() {
	local rule_id="${1:-gate}"
	local message="${2:-gate failed}"
	local file="${3:-}"
	local line="${4:-}"
	_gate_append_finding "${rule_id}" "error" "${message}" "${file}" "${line}"
	echo "FAIL ${rule_id}: ${message}" >&2
}

gate_warn() {
	local rule_id="${1:-gate}"
	local message="${2:-gate warning}"
	local file="${3:-}"
	local line="${4:-}"
	_gate_append_finding "${rule_id}" "warning" "${message}" "${file}" "${line}"
	echo "WARN ${rule_id}: ${message}" >&2
}

gate_path_ignored() {
	local rel_path="${1#./}"
	"${SHIPGATE_PYTHON:-python3}" -m shipgate.gates.ignore "${rel_path}"
}

gate_finish() {
	if ((GATE_FINDING_COUNT > 0)); then
		echo "gate '${GATE_NAME}' failed with ${GATE_FINDING_COUNT} finding(s)" >&2
		exit 1
	fi
	exit 0
}
