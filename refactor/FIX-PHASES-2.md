# Refactor Fix Phases 2

## Phase 4: Safety / Loop Hoist

- [x] Disable default `hoist-statement-from-loop` findings until the rule can prove safety.
- [x] Add regression coverage for sampled semantics-breaking loop-hoist patterns.
- [x] Run `uv run pytest refactor/tests -q`.
- [x] Run `timeout 30 env PYTHONPATH=refactor/src uv run python -m refactor check refactor/tests/test_protocol.py`.
- [x] Commit `fix(refactor): phase 4 — gate unsafe loop hoist`.

## Phase 5: Locations / Body Rules

- [x] Route `BodySequenceRewriteRule` hits through location-aware recording.
- [x] Route `BodyCleanupRule` hits through location-aware recording.
- [x] Add regression coverage for non-null locations on representative body-sequence and cleanup rules.
- [x] Run `uv run pytest refactor/tests -q`.
- [x] Run `timeout 30 env PYTHONPATH=refactor/src uv run python -m refactor check refactor/tests/test_protocol.py`.
- [x] Commit `fix(refactor): phase 5 — body-sequence hit locations`.

## Phase 6: Performance / Bounded Check

- [x] Reduce default check work enough for bounded `src/shipgate` smoke use.
- [x] Add focused regression or smoke coverage for the performance path.
- [x] Run `uv run pytest refactor/tests -q`.
- [x] Run `timeout 30 env PYTHONPATH=refactor/src uv run python -m refactor check refactor/tests/test_protocol.py`.
- [x] Try `timeout 60 env PYTHONPATH=refactor/src uv run python -m refactor check src/shipgate`.
- [x] Commit `fix(refactor): phase 6 — check performance budget`.
