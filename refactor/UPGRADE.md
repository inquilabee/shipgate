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

## Phase 2

Upgrade ten more expression/call stubs to narrow suggest-only libcst matchers.

- `chain-compares`: `BooleanOpRewriteRule` detects adjacent `and` comparisons
  sharing the middle operand.
- `collection-to-bool`: `CallRewriteRule` detects raw `len(collection)` calls and
  suggests `bool(collection)`.
- `equality-identity`: `ComparisonRewriteRule` detects identity comparison against
  non-singleton value literals.
- `flip-comparison`: `ComparisonRewriteRule` moves literal operands to the right side
  and reverses ordered operators.
- `or-if-exp-identity`: `IfExpRewriteRule` detects `x if x else y`.
- `remove-none-from-default-get`: `CallRewriteRule` detects `dict.get(key, None)`.
- `remove-redundant-boolean`: `CallRewriteRule` detects `bool(expr)`.
- `simplify-len-comparison`: `ComparisonRewriteRule` detects `len(x)` comparisons
  against zero.
- `use-datetime-now-not-today`: `CallRewriteRule` detects zero-argument
  `datetime.today()` calls.
- `use-getitem-for-re-match-groups`: `CallRewriteRule` detects `match.group(index)`.

All phase 2 rules remain `safe_apply=False` pending explicit round-trip apply tests.
