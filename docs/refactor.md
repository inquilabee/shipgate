# Refactor

ShipGate ships a **refactor** tool in the same wheel: AST-based rules for
structural Python cleanup (imports, naming, test patterns, optional GPSG packs).
It is separate from the catalog — no `shipgate check` tool entry, no PolicyGate
coupling.

Invoke it as `shipgate refactor …` or `python -m refactor …` (same CLI; the
module form is handy in src-layout dogfood and pre-commit hooks).

## Mental model

- **`check`** — detect issues; print JSON hits to stdout; exit `1` when hits exist
- **`fix`** — apply rules with `apply_mode=auto`; print changed file paths
- **`list`** — tab-separated inventory of registered rules
- **`explain`** — human-readable rule detail with catalog examples

Default `check` reports **auto** (blocking) rules only. Pass `--strict` to include
**hint** rules as well.

## Commands

```bash
shipgate refactor check .
shipgate refactor check --strict src
shipgate refactor fix src
shipgate refactor list
shipgate refactor explain default-get
```

Equivalent module invocation:

```bash
python -m refactor check --strict src tests/refactor
python -m refactor fix src
```

### Check

```bash
shipgate refactor check
shipgate refactor check --strict .
shipgate refactor check src app/
```

Output is indented JSON (rule id, path, line, message, and related fields).
Exit `0` when clean; `1` when hits remain.

### Fix

```bash
shipgate refactor fix src
shipgate refactor fix app/models.py
```

Only **auto** rules run. Hint-only findings require manual edits or a different
rule with `apply_mode=auto`.

### List and explain

```bash
shipgate refactor list
shipgate refactor list --enable gpsg
shipgate refactor explain duplicate-import
```

`list` prints one rule per line (id, kind, inventory status, apply mode, optional
pack/tag columns). `explain` prints summary, rationale, and before/after examples
from the rule inventory.

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

Refactor is not part of `shipgate check` suites. Add it explicitly when you want
structural rules alongside catalog gates:

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

## See also

- [Usage](usage.md) — catalog commands (`install`, `format`, `check`)
- [Architecture](architecture.md) — refactor is outside the catalog pipeline
