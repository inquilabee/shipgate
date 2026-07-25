# Agents and Maintainers

ShipGate is a portable, metadata-driven quality-gate orchestrator. Projects declare policy; ShipGate executes tools through catalog metadata, Execution Requests, and canonical reports.

## Start here

| Layer | Path |
| -------------------- | ---------------------------------------------------------------- |
| Agent rules | `.cursor/rules/` — always-on; override skills when they conflict |
| Gates contract | `.cursor/rules/gates.mdc` |
| Architecture | `docs/architecture.md` |
| Usage (consumer) | `docs/usage.md` |
| Check flow (tool YAML → run) | `docs/check-flow.md` |
| Option mappings | `docs/res/config.md` |

## Commands

Run ShipGate and tests via `uv run` (not bare `pytest` or `shipgate`):

```bash
uv sync --group dev
uv run shipgate init            # or: shipgate init yaml
uv run shipgate init pyproject  # merge [tool.shipgate] into pyproject.toml
uv run shipgate install
uv run shipgate update          # reinstall suite tools to catalog pins
uv run shipgate check --target .
uv run shipgate format --target .
uv run shipgate list suites
uv run shipgate list tools --tag security
uv run pytest tests/unit -q
uv run pytest tests/frontend -q          # report UI TestClient (no browser)
uv run pytest -m integration
uv run pytest -m ui -q                   # Playwright Chromium (opt-in; not in default suite)
# make test-ui                           # install Chromium + run -m ui
make install-hooks   # pre-commit
make check-commit    # canonical dogfood gate (see below)
make docker-test     # fresh-machine smoke (Docker; network for tool pins)
# SHIPGATE_DOCKER_DOGFOOD=0 make docker-test  # Phase A only
```

Default `pytest` / `make test` excludes `@pytest.mark.ui` (no browser binary required).

## Dogfooding (this repo)

Gates apply to the full codebase with no legacy carve-outs; see `.cursor/rules/quality.mdc` (Dogfooding).

**Project root:** directory where `shipgate init` was run. Discovery precedence: explicit `--target` / API `project_root` > `.shipgate/cache/.env` (`SHIPGATE_ROOT`) > walk-up (`.shipgate/shipgate.yaml`, legacy root YAML, `.git`, `pyproject.toml`).

**Policy source:** `.shipgate/cache/.env` records `SHIPGATE_POLICY=yaml` or `SHIPGATE_POLICY=pyproject` from init. When both `.shipgate/shipgate.yaml` and `[tool.shipgate]` exist, YAML overrides on conflicts (pyproject is the merge base). `SHIPGATE_POLICY` hints the primary source when discovery is ambiguous.

**Default suite:** `full` (from `.shipgate/shipgate.yaml` or `[tool.shipgate]` in `pyproject.toml`).

**Pre-commit:** mirrors format → check; only non-catalog hooks (e.g. djlint for Jinja) stay separate.

**`shipgate init` scaffolds:** `.shipgate/shipgate.yaml` (yaml mode) or `[tool.shipgate]` in `pyproject.toml` (pyproject mode), `.shipgate/catalog/`, `.shipgate/gates/`, `.shipgate/configs/`, `.shipgate/.gitignore`, `.shipgate/cache/.env` (`SHIPGATE_ROOT`, `SHIPGATE_POLICY`). Example pyproject policy: `.shipgate/pyproject.toml.example`.

**Canonical gate (`make check-commit`):** `uv sync --group dev` → `shipgate install` → `shipgate format --target .` → `shipgate check --target .`

**`env: managed`:** creates `.shipgate/tools/python/` venv; `init` writes `.shipgate/.gitignore` (ignores `cache/`, `reports/`, `tools/`, etc.)

- Use Python **3.13** locally (see `.python-version`). `semgrep` does not run on 3.14 yet; library `requires-python` stays `>=3.11,<3.15`.
- Binary tools must be on `PATH` for the full suite: `gitleaks`, `markdownlint`, `shfmt`, `yamlfmt` (google/yamlfmt), `shellcheck`.
- Reports root: `.shipgate/reports/` (not repo-root `reports/`).
- Bundled catalog under `src/shipgate/catalog/bundled/` is product defaults — do not hardcode repo paths there.
- Project overrides: `.shipgate/shipgate.yaml`, `[tool.shipgate]` in `pyproject.toml`, `.shipgate/gates/`, `.shipgate/configs/` (tool config home; scaffold with `shipgate init` or `shipgate configs sync`).

## Architecture layers (one responsibility each)

```text
domain/ → config/ → catalog/ → planning/ → adapter/ → runtime/ → normalize/ → formatters/ → app.py → cli.py
```

| Parallel package | Responsibility |
| --- | --- |
| `policy/` | Bundled `PolicyGate` modules (`module:` catalog tools) |
| `gates/` | Script-gate runtime and local-gate discovery |
| `frontend/` | Report UI; reads canonical reports only |
| `project/` | `init` / scaffold / project Python helpers |
| `registries/` | Shared ID registries |
| `core/` | Shared process/path utilities |
| `plugins/` | Deferred stub (Decision 005) |

**Boundary rule:** Does this belong in project policy, catalog metadata, planning, execution, normalization, or formatting? If unclear, stop.

## Agent rules

- Read `.cursor/rules/` before substantial edits.
- Plan before multi-file or public API changes.
- Write regression tests before production fixes.
- Do not commit/push/PR unless explicitly asked.
- Never bypass hooks.
- Verify with fresh command output before claiming done.
