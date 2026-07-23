#!/usr/bin/env bash
# Stage a ShipGate repo snapshot for the optional dogfood phase in docker-test.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGING="$ROOT/docker/dogfood-staging"

rm -rf "$STAGING"
mkdir -p "$STAGING"

rsync -a \
	--exclude='.git/' \
	--exclude='.shipgate/reports/' \
	--exclude='.shipgate/tools/' \
	--exclude='docker/dogfood-staging/' \
	--exclude='**/__pycache__/' \
	--exclude='**/*.egg-info/' \
	--exclude='.venv/' \
	--exclude='.cursor/' \
	"$ROOT/" "$STAGING/"
