# Agents and Maintainers

ShipGate is a portable, metadata-driven quality-gate orchestrator. Projects declare policy; ShipGate executes tools through catalog metadata, Execution Requests, and canonical reports.

## Start here

| Layer | Path |
|-------|------|
| Agent rules | `.cursor/rules/` — always-on; override skills when they conflict |
| Design | `docs/sdd.md` |
| ADR index | `docs/adr-support.md` |
| Implementation guide | `docs/implementation.md` |
| Option mappings | `docs/res/config.md` |

## Commands

```bash
pip install -e .
pytest tests/unit -q
pytest -m integration
shipgate install
shipgate check
shipgate format
shipgate list suites
make install-hooks   # pre-commit
make check-commit    # format + full suite (dogfood)
```

## Dogfooding (this repo)

- Use Python **3.13** locally (see `.python-version`). `semgrep` does not run on 3.14 yet; library `requires-python` stays `>=3.11,<3.15`.
- `make check-commit` and pre-commit run apply formatters, then `shipgate check --suite full`.
- Binary tools must be on `PATH` for the full suite: `gitleaks`, `markdownlint`, `shfmt`, `yamlfmt` (google/yamlfmt), `shellcheck`.
- Reports root: `.shipgate/reports/` (not repo-root `reports/`).
- Bundled catalog under `src/shipgate/catalog/bundled/` is product defaults — do not hardcode repo paths there.
- Project overrides: `shipgate.yaml`, `.shipgate/gates/`, `.shipgate/configs/`.

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
