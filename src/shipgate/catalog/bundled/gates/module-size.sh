#!/usr/bin/env bash
# Module size gate — portfolio and module line caps.
set -euo pipefail

# shellcheck source=/dev/null
source "${SHIPGATE_GATES_LIB:-$(shipgate gates lib-path)}"

gate_init "module-size"

PORTFOLIO_MAX="${GATE_PORTFOLIO_MAX_LINES:-1000}"
MODULE_MAX="${GATE_MODULE_MAX_LINES:-${GATE_NEW_FILE_MAX_LINES:-500}}"
ALLOWLIST="${GATE_ALLOWLIST_FILE-}"
IFS=' ' read -r -a SCAN_ROOTS <<<"${GATE_SCAN_ROOTS:-.}"

count_non_blank_lines() {
	local file="$1"
	grep -cve '^[[:space:]]*$' "${file}" || true
}

is_allowlisted() {
	local rel="$1"
	[[ -n ${ALLOWLIST} && -f ${ALLOWLIST} ]] || return 1
	"${SHIPGATE_PYTHON:?SHIPGATE_PYTHON is required}" -m shipgate.policy.path_allowlist --file "${ALLOWLIST}" --contains "${rel}"
}

check_module_file() {
	local rel="$1"
	local file="${rel}"
	if gate_path_ignored "${rel}"; then
		return 0
	fi
	if is_allowlisted "${rel}"; then
		return 0
	fi
	local loc
	loc="$(count_non_blank_lines "${file}")"
	if ((loc > MODULE_MAX)); then
		gate_fail "module-size" "${rel} has ${loc} lines (module cap ${MODULE_MAX})" "${rel}" "1"
	elif ((loc > PORTFOLIO_MAX)); then
		gate_fail "module-size" "${rel} has ${loc} lines (portfolio cap ${PORTFOLIO_MAX})" "${rel}" "1"
	fi
}

if [[ -n ${SHIPGATE_SCOPE_PATHS-} ]]; then
	while IFS= read -r file; do
		[[ -n ${file} ]] || continue
		check_module_file "${file}"
	done <<<"${SHIPGATE_SCOPE_PATHS}"
else
	for scan_root in "${SCAN_ROOTS[@]}"; do
		[[ -d ${scan_root} ]] || continue
		while IFS= read -r -d '' file; do
			rel="${file#./}"
			check_module_file "${rel}"
		done < <(find "${scan_root}" -name '*.py' -print0)
	done
fi

gate_finish
