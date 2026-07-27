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

`fix` / `fix_paths` only call `apply` when `safe_apply` is true. For each file, rules run
in registry order on the latest source; each safe rule re-detects before applying. If
`apply` returns source that still matches the rule, the rewrite is skipped (partial or
failed transforms never get written).

Eligible rules must pass a round-trip: `detect → apply → detect` is empty on the
rewritten source. Use libcst node transforms, not `str.replace`. Shared helper:

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

#### Native rules eligible for `fix` (`safe_apply=True`)

| Rule ID | Summary |
| --- | --- |
| `default-get` | `d[key] if key in d else default` → `d.get(key, default)` |
| `dict-literal` | empty `dict()` → `{}` |
| `tuple-literal` | empty `tuple()` → `()` |
| `remove-redundant-pass` | drop trailing `pass` in blocks |
| `use-len` | `len(x) == 0` → `not x` (and related) |
| `min-max-identity` | `a if a < b else b` → `min(a, b)` / `max` |
| `aug-assign` | `x = x + n` → `x += n` |
| `none-compare` | `x == None` → `x is None` |
| `boolean-if-exp-identity` | `True if c else False` → `c` |
| `simplify-boolean-comparison` | `x == True` → `x` |
| `collection-into-set` | membership on list/tuple literal → set literal |
| `yield-from` | `for x in ys: yield x` → `yield from ys` |
| `bin-op-identity` | `x + 0` / `x * 1` → `x` |

#### Deny-list (`safe_apply=False`)

These rules detect and suggest only; `fix` leaves them untouched.

| Rule ID | Why not auto-apply |
| --- | --- |
| `default-mutable-arg` | inserts body init; needs human review (`RuleKind.SUGGESTION`) |
| `merge-nested-ifs` | control-flow reshape; readability trade-off |
| `inline-immediately-returned-variable` | may hurt step-through debugging |
| `use-next` | `next(iter(...))` raises on empty iterable |
| `identity-comprehension` | changes evaluation semantics for generators |
| `for-index-replacement` | loop structure change; not always clearer |
| `remove-unreachable-code` | deletes statements; high impact |
| Ruff bridges (`list-literal`, `avoid-builtin-shadow`, …) | delegated fixes; no native libcst `apply` |

Set `safe_apply=True` only after a libcst transformer round-trip test proves
`detect(apply(source))` is empty.
