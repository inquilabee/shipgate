# Isolated Sourcery-parity refactor engine

Not wired into ShipGate suites/catalog yet. Uses the **repo root** `uv` environment
(`libcst` is in the root `dev` dependency group).

## Commands

```bash
# from repo root
uv sync --group dev
uv run pytest refactor/tests -q
uv run python -m refactor list
uv run python -m refactor check path/to/file.py
uv run python -m refactor fix path/to/file.py
```

## Add a rule

1. Create `refactor/src/refactor/rules/native/your_rule.py` (or `rules/bridge/`).
1. Implement `RefactorRule` (`detect`, optional `apply`, `safe_apply`).
1. Register the instance in `registry.py`.
1. Add golden fixtures + tests under `refactor/tests/`.
