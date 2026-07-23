#!/usr/bin/env bash
# ShipGate fresh-machine integration test — runs inside Docker container.
set -uo pipefail

LOG_DIR=/workspace/logs
mkdir -p "$LOG_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

RUN_DOGFOOD="${SHIPGATE_DOCKER_DOGFOOD:-1}"

step() {
	echo ""
	echo "================================================================"
	echo ">>> $*"
	echo "================================================================"
}

run_cmd() {
	local label="$1"
	shift
	local logfile="$LOG_DIR/$(echo "$label" | tr ' /:' '___').log"
	echo ""
	echo "--- $label ---"
	echo "Command: $*"
	local start end elapsed rc
	start=$(date +%s)
	set +e
	"$@" > >(tee "$logfile") 2>&1
	rc=$?
	set -e
	end=$(date +%s)
	elapsed=$((end - start))
	if [[ $rc -eq 0 ]]; then
		echo -e "${GREEN}PASS${NC} ($label) — ${elapsed}s — log: $logfile"
	else
		echo -e "${RED}FAIL${NC} ($label) — exit $rc — ${elapsed}s — log: $logfile"
	fi
	RESULTS+=("$label|$rc|${elapsed}s")
	return 0
}

POLICY_YAML=".shipgate/shipgate.yaml"

RESULTS=()

step "Environment"
echo "Python: $(python --version 2>&1)"
echo "ShipGate: $(shipgate --help 2>&1 | head -1 || true)"
echo "git: $(git --version)"
echo "node: $(node --version 2>/dev/null || echo MISSING)"
echo "npm: $(npm --version 2>/dev/null || echo MISSING)"
echo "go: $(go version 2>/dev/null || echo MISSING)"
echo "Platform: $(uname -m) $(uname -s)"
echo "Dogfood phase: ${RUN_DOGFOOD}"

# ---------------------------------------------------------------------------
# Phase A: brand-new empty project adopting ShipGate
# ---------------------------------------------------------------------------
step "PHASE A — Fresh empty project"

FRESH=/workspace/fresh-project
rm -rf "$FRESH"
mkdir -p "$FRESH"
cd "$FRESH"
git init -q
git config user.email "test@shipgate.local"
git config user.name "ShipGate Docker Test"

cat >main.py <<'PY'
"""Minimal sample project."""


def greet(name: str) -> str:
    return f"hello, {name}"
PY

cat >README.md <<'MD'
# Fresh Project

A minimal project for ShipGate integration testing.
MD

git add -A
git commit -q -m "initial commit"

run_cmd "A1 shipgate init" shipgate init
echo "--- shipgate.yaml ---"
cat "$POLICY_YAML"
echo "--- .shipgate/configs (first 20) ---"
find .shipgate/configs -type f 2>/dev/null | head -20 || true

sed -i 's/^suite: standard/suite: full/' "$POLICY_YAML"
echo "--- updated shipgate.yaml ---"
cat "$POLICY_YAML"

run_cmd "A2 shipgate install --suite full" shipgate install --suite full
echo "--- install manifest ---"
cat .shipgate/tools/manifest.json 2>/dev/null || echo "(no manifest)"
echo "--- managed binaries ---"
ls -la .shipgate/tools/bin/ 2>/dev/null || echo "(no bin dir)"

run_cmd "A3 shipgate format" shipgate format
run_cmd "A4 shipgate check --suite full" shipgate check --suite full

# ---------------------------------------------------------------------------
# Phase B: Dogfood on ShipGate repo snapshot (optional)
# ---------------------------------------------------------------------------
if [[ $RUN_DOGFOOD == "1" ]]; then
	step "PHASE B — ShipGate repo dogfood subset"

	DOGFOOD=/workspace/dogfood-repo
	rm -rf "$DOGFOOD"
	cp -a /workspace/dogfood/. "$DOGFOOD/"
	cd "$DOGFOOD"
	git init -q
	git config user.email "test@shipgate.local"
	git config user.name "ShipGate Docker Test"
	git add -A
	git commit -q -m "dogfood subset"

	run_cmd "B1 shipgate install" shipgate install
	echo "--- project python env for ty ---"
	python3 -m venv .venv
	.venv/bin/pip install -q -e ".[server]"
	echo "--- install manifest ---"
	cat .shipgate/tools/manifest.json 2>/dev/null || echo "(no manifest)"
	echo "--- managed binaries ---"
	ls -la .shipgate/tools/bin/ 2>/dev/null || echo "(no bin dir)"

	run_cmd "B2 shipgate format --target ." shipgate format --target .
	run_cmd "B3 shipgate check --suite python-quality --target src/shipgate/domain" \
		shipgate check --suite python-quality --target src/shipgate/domain
else
	echo ""
	echo "Skipping PHASE B (SHIPGATE_DOCKER_DOGFOOD=${RUN_DOGFOOD})"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step "SUMMARY"
pass=0
fail=0
for row in "${RESULTS[@]}"; do
	IFS='|' read -r label rc elapsed <<<"$row"
	if [[ $rc -eq 0 ]]; then
		echo -e "${GREEN}PASS${NC}  $label ($elapsed)"
		pass=$((pass + 1))
	else
		echo -e "${RED}FAIL${NC}  $label (exit $rc, $elapsed)"
		fail=$((fail + 1))
	fi
done
echo ""
echo "Total: $pass passed, $fail failed"
echo "Logs: $LOG_DIR"

if [[ $fail -gt 0 ]]; then
	exit 1
fi
