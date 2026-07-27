# Refactor

Isolated Python refactor engine. It is not wired into ShipGate suites or the
bundled catalog yet, and it uses the repo-root `uv` environment.

## Commands

Run from the repository root:

```bash
uv sync --group dev
uv run pytest refactor/tests -q

PYTHONPATH=refactor/src uv run python -m refactor list
PYTHONPATH=refactor/src uv run python -m refactor check path/to/file.py
PYTHONPATH=refactor/src uv run python -m refactor fix path/to/file.py
```

`PYTHONPATH=refactor/src` is required for `python -m refactor` because this package is
kept isolated from the main ShipGate package.

## Inventory

Rule IDs and implementation status live in `refactor/inventory/rule_ids.yaml`.
Ruff bridge rules are listed by `refactor list` as delegated entries; `check`
does not execute Ruff for them.

## Safe Apply

`fix` only runs rules with `safe_apply=True`. A rule should set `safe_apply=True` only
after tests prove `detect -> apply -> detect` is empty for the rewritten source. Use
LibCST transforms for rewrites, not string replacement.

For each file, safe rules run in registry order on the latest source and re-detect before
applying. If a rewrite still matches the same rule, it is skipped instead of written.
