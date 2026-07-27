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

## Phase 3

Upgrade ten collection, string, and fallback expression stubs to suggest-only libcst
matchers.

- `collection-builtin-to-comprehension`: `CallRewriteRule` detects
  `dict((k, v) for ...)` generator calls.
- `comprehension-to-generator`: `CallRewriteRule` detects list comprehensions passed to
  `any()` or `all()`.
- `list-comprehension`: `CallRewriteRule` detects `list(x for ...)`.
- `set-comprehension`: `CallRewriteRule` detects `set(x for ...)`.
- `sum-comprehension`: `CallRewriteRule` detects list comprehensions passed to `sum()`.
- `unwrap-iterable-construction`: `CallRewriteRule` detects redundant literal wrappers
  such as `list([1, 2])`.
- `skip-sorted-list-construction`: `CallRewriteRule` detects `sorted(list(items))`.
- `use-file-iterator`: `CallRewriteRule` detects zero-argument `.readlines()` calls.
- `simplify-substring-search`: `ComparisonRewriteRule` detects `find()` comparisons
  against `-1`.
- `use-or-for-fallback`: `IfExpRewriteRule` detects `x if x else y`.

All phase 3 rules remain `safe_apply=False` pending explicit round-trip apply tests.

## Phase 4

Upgrade ten call, comparison, generator, and pandas expression stubs to suggest-only
libcst matchers.

- `max-min-default`: `IfExpRewriteRule` detects `max(x) if x else default` and
  `min(x) if x else default`.
- `remove-redundant-condition`: `IfExpRewriteRule` detects identical if-expression
  branches.
- `convert-any-to-in`: `CallRewriteRule` detects `any(item == value for item in items)`.
- `invert-any-all`: `UnaryOpRewriteRule` detects `not any(generator)` /
  `not all(generator)`.
- `invert-any-all-body`: `UnaryOpRewriteRule` uses the same inversion matcher.
- `use-count`: `CallRewriteRule` detects `sum(1 for item in items if item == value)`.
- `dataframe-append-to-concat`: `CallRewriteRule` detects `.append(other)` and suggests
  `pd.concat([df, other])`.
- `use-isna`: `ComparisonRewriteRule` detects pandas-style null comparisons.
- `pandas-avoid-inplace`: `CallRewriteRule` detects explicit `inplace=True` arguments.
- `remove-dict-items`: `CallRewriteRule` detects `dict(data.items())`.

All phase 4 rules remain `safe_apply=False` pending explicit round-trip apply tests.

## Phase 5

Upgrade ten dictionary, comparison, pandas, and if-expression stubs to suggest-only
libcst matchers.

- `remove-duplicate-dict-key`: reuses the duplicate dict literal matcher with suggestion
  kind.
- `merge-isinstance`: `BooleanOpRewriteRule` detects repeated `isinstance()` checks.
- `merge-is-instance`: uses the same shared `isinstance()` merge matcher.
- `simplify-string-len-comparison`: reuses the len comparison matcher for strings.
- `replace-apply-with-method-call`: `CallRewriteRule` detects `series.apply(str.method)`.
- `replace-apply-with-numpy-operation`: `CallRewriteRule` detects
  `series.apply(np.func)`.
- `simplify-numeric-comparison`: `ComparisonRewriteRule` detects `x - y` comparisons
  against zero.
- `return-identity`: `IfExpRewriteRule` detects identical if-expression branches.
- `swap-if-expression`: `IfExpRewriteRule` detects if-expressions with negated tests.
- `swap-if-else-branches`: uses the same negated-test branch swap matcher.

All phase 5 rules remain `safe_apply=False` pending explicit round-trip apply tests.

## Phase 6

Upgrade ten comprehension, string, body-cleanup, and exception stubs to suggest-only
libcst matchers.

- `dict-comprehension`: reuses the dict comprehension matcher.
- `simplify-generator`: reuses the list-comprehension-to-generator matcher.
- `use-any`: `CallRewriteRule` detects `bool([expr for ...])`.
- `use-string-remove-affix`: `SubscriptRewriteRule` detects affix-removal slices.
- `simplify-fstring-formatting`: `FormattedStringRewriteRule` removes redundant `!s`.
- `use-join`: `BinaryOpRewriteRule` detects simple string concatenation chains.
- `remove-pass-body`: `BodyCleanupRule` detects pass-only bodies.
- `remove-empty-nested-block`: `BodyCleanupRule` detects pass-only nested blocks.
- `remove-redundant-continue`: `BodyCleanupRule` detects trailing `continue`.
- `simplify-single-exception-tuple`: custom visitor detects one-item exception tuples.

All phase 6 rules remain `safe_apply=False` pending explicit round-trip apply tests.

## Phase 7

Upgrade ten statement/control-flow stubs to suggest-only libcst matchers with shared
statement replacement helpers.

- `merge-else-if-into-elif`: `IfRewriteRule` detects `else: if ...` blocks.
- `remove-unnecessary-else`: `IfRewriteRule` detects `else` after terminal if bodies.
- `useless-else-on-loop`: `ForRewriteRule` detects loop `else` blocks and flattens them.
- `hoist-if-from-if`: `IfRewriteRule` detects single nested if bodies and merges tests.
- `swap-nested-ifs`: reuses the nested-if merge matcher.
- `remove-pass-elif`: `IfRewriteRule` removes pass-only elif branches.
- `remove-redundant-if`: `IfRewriteRule` detects boolean-returning if/else statements.
- `ternary-to-if-expression`: `IfRewriteRule` detects matching assignment targets in both
  branches.
- `while-guard-to-condition`: `WhileRewriteRule` detects `while True` with a leading break
  guard.
- `hoist-statement-from-if`: `IfRewriteRule` detects identical trailing branch statements.

All phase 7 rules remain `safe_apply=False` pending explicit round-trip apply tests.

## Phase 8

Upgrade ten call, loop, small-statement, and try stubs to suggest-only libcst matchers.

- `aware-datetime-for-utc`: `CallRewriteRule` detects `datetime.utcnow()`.
- `remove-unused-enumerate`: `ForRewriteRule` detects unused enumerate indexes.
- `replace-dict-items-with-values`: `ForRewriteRule` detects unused keys from `.items()`.
- `merge-assign-and-aug-assign`: `SimpleStatementLineRewriteRule` detects self-updates.
- `dict-assign-update-to-union`: shared small-statement matcher detects `.update(...)`.
- `simplify-dictionary-update`: reuses the dictionary union assignment matcher.
- `use-dictionary-union`: `CallRewriteRule` detects `dict(left, **right)`.
- `raise-specific-error`: `SimpleStatementLineRewriteRule` detects `raise Exception`.
- `remove-redundant-exception`: `SimpleStatementLineRewriteRule` detects `raise ... from None`.
- `use-contextlib-suppress`: `TryRewriteRule` detects try/except-pass blocks.

All phase 8 rules remain `safe_apply=False` pending explicit round-trip apply tests.
