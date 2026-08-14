# Vision

## Who

Solo or small-team Python maintainers (humans and coding agents) who want one
policy and one command surface instead of hand-rolled CI glue for every linter.

## Product

ShipGate is a portable quality-gate orchestrator: `shipgate init` / `install` /
`format` / `check`, plus `shipgate refactor` for structural AST rules. One
project policy and a metadata-driven catalog run the same suites locally, in
pre-commit, and in CI. Optional `shipgate serve` browses canonical JSON reports.

## Not this

Not a replacement for pytest, not a hosted SaaS, not a layout enforcer that
forces consumer repos into `src/`, and not a swarm of public APIs or CLIs.

## Success

A maintainer can init, install, format, and check a real Python repo with the
bundled suites; agents and humans hit the same gates; reports land under
`.shipgate/reports/` without weakening thresholds to go green.
