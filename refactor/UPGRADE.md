# Native Matcher Upgrade

## Phase 1

Upgrade ten low-risk expression and literal stubs to suggest-only libcst matchers.

- `compare-via-equals`: `CallRewriteRule` detects `obj.__eq__(other)` and suggests
  `obj == other`.
- `merge-comparisons`: `BooleanOpRewriteRule` detects adjacent `and` comparisons
  sharing the middle operand.
- `remove-duplicate-set-key`: `SetRewriteRule` detects repeated rendered set elements.
- `remove-redundant-constructor-in-dict-union`: `BinaryOpRewriteRule` unwraps
  `dict(x)` operands around dictionary union.
- `non-equal-comparison`: `UnaryOpRewriteRule` detects `not (a == b)` and
  `not (a != b)`.
- `remove-dict-keys`: `CallRewriteRule` detects zero-argument `.keys()` calls.
- `simplify-empty-collection-comparison`: `ComparisonRewriteRule` detects equality
  checks against empty literals.
- `remove-duplicate-key`: `DictRewriteRule` detects duplicate literal keys and keeps
  the last value.
- `remove-unnecessary-cast`: `CallRewriteRule` detects `cast(T, value)` and
  `typing.cast(T, value)`.
- `simplify-constant-sum`: `BinaryOpRewriteRule` folds integer literal `+` and `-`
  expressions.

All phase 1 rules remain `safe_apply=False` pending explicit round-trip apply tests.
