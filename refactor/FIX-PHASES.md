# Refactor Fix Phases

## Phase 1: Correctness / Crashes

- [x] Parse Python integer literals with base-aware semantics in `simplify-constant-sum`.
- [x] Apply the same integer parsing hardening to similar native literal helpers.
- [x] Add regression coverage for decimal, underscored, binary, octal, and hex integers.
- [x] Verify `PYTHONPATH=refactor/src uv run python -m refactor check src/shipgate refactor/src/refactor` exits without traceback.
- [x] Run `uv run pytest refactor/tests -q`.
- [x] Commit `fix(refactor): phase 1 — prevent literal crashes`.

## Phase 2: Signal Quality

- [ ] Scope test-only structural rules to test files.
- [ ] Replace broad `introduce-default-else` hits with a focused default-assignment pattern.
- [ ] Disable placeholder or unsafe default suggestions for `last-if-guard`, `extract-method`, and `class-extract-method`.
- [ ] Document default signal-quality policy in the refactor README.
- [ ] Run `uv run pytest refactor/tests -q`.
- [ ] Commit `fix(refactor): phase 2 — improve default signal quality`.

## Phase 3: Parity / UX

- [ ] Populate hit line and column from LibCST metadata where feasible.
- [ ] Make standalone path collection respect gitignore-style ignored directories and generated caches.
- [ ] Clarify Ruff bridge behavior in CLI/list output and documentation.
- [ ] Add focused regression coverage for positions, path walking, and bridge UX.
- [ ] Run `uv run pytest refactor/tests -q`.
- [ ] Re-run the full dogfood check on `src/shipgate` and `refactor/src/refactor`.
- [ ] Commit `fix(refactor): phase 3 — improve refactor UX`.
