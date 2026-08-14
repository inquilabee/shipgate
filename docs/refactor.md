# Refactor

AST rules for structural Python cleanup (imports, naming, test patterns, optional
packs). Same wheel as ShipGate, separate from catalog suites — not part of
`shipgate check`.

Use `shipgate refactor …` or `python -m refactor …` (same CLI).

## Try this

```bash
shipgate refactor check .
shipgate refactor check --strict src
shipgate refactor fix src
shipgate refactor list
shipgate refactor explain default-get
```

Module form (handy in src-layout dogfood and hooks):

```bash
python -m refactor check --strict src tests/refactor
python -m refactor fix src
```

## What you should see

| Command | Success | Failure / notes |
| --- | --- | --- |
| `check` | Exit `0`; stdout is `[]` or an empty hit list | Exit `1`; indented JSON hits (rule id, path, line, message) |
| `check --strict` | Same, but includes **hint** rules | Default `check` reports **auto** (blocking) rules only |
| `fix` | Prints changed file paths; exit `0` when done | Only **auto** rules apply; hints need a manual edit or another auto rule |
| `list` | One rule per line (id, kind, apply mode, …) | Use `--enable` to include optional packs |
| `explain <id>` | Summary, rationale, before/after examples | Unknown id → non-zero / error text |

Example hit shape (fields vary by rule):

```json
[
  {
    "rule_id": "duplicate-import",
    "path": "src/pkg/mod.py",
    "line": 3,
    "message": "…"
  }
]
```

## Paths and scope

With no paths, or with `.` at the project root, refactor prefers a **dogfood
scope** when those directories exist: `src/` and `tests/refactor/`. That keeps
fixture-heavy trees such as `tests/unit/` out of the default scan — those files
trip test-only rules by design.

Pass explicit paths to scan elsewhere:

```bash
shipgate refactor check tests/unit
shipgate refactor check app/ lib/
```

## Optional packs

GPSG and other tagged packs stay off unless enabled:

```bash
shipgate refactor check --enable gpsg
shipgate refactor check --enable gpsg-import,gpsg-naming src
```

`--enable` accepts comma-separated values or repeats (`--enable gpsg --enable gpsg-naming`).

## CI and pre-commit

Refactor is not part of `shipgate check` suites. Add it explicitly:

```yaml
repos:
  - repo: local
    hooks:
      - id: shipgate-refactor
        name: shipgate refactor
        entry: shipgate refactor check --strict
        language: system
        types: [python]
```

For src-layout projects, `python -m refactor check --strict src tests/refactor`
matches the ShipGate maintainer gate (`make check-commit`).

## Next

- Catalog commands → [Usage](usage.md)
- First install → [Quick start](quickstart.md)
