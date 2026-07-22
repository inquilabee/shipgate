# Agents and Maintainers

ShipGate is a portable, metadata-driven quality-gate orchestrator. Projects declare policy; ShipGate executes tools through catalog metadata, Execution Requests, and canonical reports.

## Start here

| Layer | Path |
| --- | --- |
| Agent rules | `.cursor/rules/` — always-on; override skills when they conflict |
| Gates contract | `.cursor/rules/gates.mdc` |
| Design | `docs/sdd.md` |
| ADR index | `docs/adr-support.md` |
| Implementation guide | `docs/implementation.md` |
| Option mappings | `docs/res/config.md` |

## Commands

Run ShipGate and tests via `uv run` (not bare `pytest` or `shipgate`):

```bash
uv sync --group dev
uv run shipgate init
uv run shipgate install
uv run shipgate check --target .
uv run shipgate format --target .
uv run shipgate list suites
uv run pytest tests/unit -q
uv run pytest -m integration
make install-hooks   # pre-commit
make check-commit    # canonical dogfood gate (see below)
make docker-test     # fresh-machine smoke test (Docker)
```

## Dogfooding (this repo)

Gates apply to the full codebase with no legacy carve-outs; see `.cursor/rules/quality.mdc` (Dogfooding).

**Project root:** directory containing `shipgate.yaml`, discovered upward from the current working directory.

**Canonical gate (`make check-commit`):** `uv sync --group dev` → `shipgate install` → `shipgate format --target .` → `shipgate check --target .`

**Default suite:** `full` (from `shipgate.yaml`).

**Pre-commit:** mirrors format → check; only non-catalog hooks (e.g. djlint for Jinja) stay separate.

**`shipgate init` scaffolds:** `shipgate.yaml`, `.shipgate/gates/`, `.shipgate/configs/`, `.shipgate/.gitignore`

**`env: managed`:** creates `.shipgate/tools/python/` venv; `init` writes `.shipgate/.gitignore`

- Use Python **3.13** locally (see `.python-version`). `semgrep` does not run on 3.14 yet; library `requires-python` stays `>=3.11,<3.15`.
- Binary tools must be on `PATH` for the full suite: `gitleaks`, `markdownlint`, `shfmt`, `yamlfmt` (google/yamlfmt), `shellcheck`.
- Reports root: `.shipgate/reports/` (not repo-root `reports/`).
- Bundled catalog under `src/shipgate/catalog/bundled/` is product defaults — do not hardcode repo paths there.
- Project overrides: `shipgate.yaml`, `.shipgate/gates/`, `.shipgate/configs/` (tool config home; scaffold with `shipgate init` or `shipgate configs sync`).

## Architecture layers (one responsibility each)

```text
domain/ → config/ → catalog/ → planning/ → adapter/ → runtime/ → normalize/ → formatters/ → app.py → cli.py
```

**Boundary rule:** Does this belong in project policy, catalog metadata, planning, execution, normalization, or formatting? If unclear, stop.

## Agent rules

- Read `.cursor/rules/` before substantial edits.
- Plan before multi-file or public API changes.
- Write regression tests before production fixes.
- Do not commit/push/PR unless explicitly asked.
- Never bypass hooks.
- Verify with fresh command output before claiming done.
