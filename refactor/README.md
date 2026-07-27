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

## Inventory

Sourcery rule IDs and parity status live in `refactor/inventory/sourcery_ids.yaml`.
Load them with `refactor.inventory.load_inventory()` (used by inventory tests and
future parity tracking).

## Add a rule

1. Create `refactor/src/refactor/rules/native/your_rule.py` (or `rules/bridge/`).
1. Implement `RefactorRule` (`detect`, optional `apply`, `safe_apply`).
1. Register the instance in `registry.py`.
1. Add golden fixtures + tests under `refactor/tests/`.

### Safe apply (`safe_apply=True`)

Use libcst node transforms, not `str.replace`. Shared helper:

```python
from refactor.cst_util import apply_with_transformer

class MyRule:
    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = hits
        return apply_with_transformer(source, MyRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_SomeNode(self, original, updated):
            ...
```

Reuse the same `match_*` / `build_*` helpers from `detect` inside the transformer so
apply rewrites every matching node in the file.
