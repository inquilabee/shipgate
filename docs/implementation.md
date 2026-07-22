# ShipGate implementation document

> **For agentic workers:** implement this document task by task. Keep changes small, test every layer before wiring it upward, and preserve the product rule from `docs/sdd.md`: ShipGate should be useful almost immediately after installation.

**Goal:** build ShipGate as an extensible, metadata-driven quality-gate orchestrator with the familiar user experience from the prior attempt: `shipgate install`, `shipgate format`, and `shipgate check`.

**Architecture:** ShipGate has a repository-policy layer, a normalized request/planning layer, and an execution/reporting layer. Project config selects policy. Catalog metadata describes tools and suites. Runtime code turns an Execution Request into a Resolved Request, serializes it into argv, executes the process, normalizes output, and formats results.

**Tech stack:** Python 3.11 through 3.14, stdlib-first runtime, `PyYAML` for YAML parsing, `pytest` for tests, `ruff` for lint/format, `ty` or `mypy` only if the project later chooses a type checker. Avoid large frameworks until the domain contracts settle.

## 1. Implementation stance

This document is intentionally concrete. It names files, responsibilities, public types, pipeline order, tests, and milestone behavior.

The current repository is documentation-only. The first implementation should not try to build every future feature from `docs/sdd.md`. It should prove one path end to end:

```text
project config
  -> workflow
  -> scope
  -> execution request
  -> resolved request
  -> one tool definition
  -> adapter
  -> executor
  -> normalizer
  -> JSON and compact formatter
```

The old `inquilabee/shipgate` attempt is a product reference, not an architecture reference. Keep the good parts:

- one small project config
- bundled suites
- managed tool installation
- quiet success
- structured failure reports
- simple commands: `install`, `format`, `check`
- a SonarQube-inspired frontend for browsing reports

Replace the weak part: tool behavior must not live as hardcoded runtime branches.

## 2. Build order

Build in this order:

1. Package skeleton and CLI shell
1. Domain models
1. Project config parser
1. Catalog model and bundled catalog loader
1. Workflow and suite resolver
1. Execution Request and Resolved Request planner
1. CLI adapter
1. Executor
1. Canonical report schema
1. Normalizers
1. Formatters
1. Managed installs
1. First bundled suite
1. CI integration behavior
1. Local gate support
1. SonarQube-inspired report frontend only after the CLI/report model is stable

Do not start with the report frontend, custom plugin API, parallel execution, or remote runners. Those depend on contracts that need to harden first.

## 3. Proposed repository layout

Create this structure:

```text
pyproject.toml
README.md
docs/
  sdd.md
  adr-support.md
  implementation.md
src/
  shipgate/
    __init__.py
    __main__.py
    cli.py
    errors.py
    paths.py
    domain/
      __init__.py
      ids.py
      modes.py
      options.py
      project.py
      catalog.py
      execution.py
      reports.py
    config/
      __init__.py
      loader.py
      schema.py
      discovery.py
    catalog/
      __init__.py
      loader.py
      validate.py
      bundled/
        catalog.yaml
        configs/
          ruff.toml
          bandit.yaml
          ty.toml
    planning/
      __init__.py
      workflow.py
      checks.py
      scopes.py
      suites.py
      requests.py
      defaults.py
    adapter/
      __init__.py
      argv.py
      serialize.py
    runtime/
      __init__.py
      executor.py
      install.py
      environment.py
      reports.py
    normalize/
      __init__.py
      base.py
      ruff.py
      generic.py
    formatters/
      __init__.py
      json.py
      compact.py
      text.py
      github.py
    gates/
      __init__.py
      init.py
      catalog.py
tests/
  unit/
  integration/
  fixtures/
```

Keep modules boring and small. If a module cannot be explained in one sentence, split it.

## 4. Package skeleton

### `pyproject.toml`

Use `src` layout.

Minimum fields:

- project name: `shipgate`
- Python range: `>=3.11,<3.15`
- console script: `shipgate = "shipgate.cli:main"`
- runtime dependency: `PyYAML`
- test dependency group: `pytest`

Suggested tool config:

```toml
[project]
name = "shipgate"
version = "0.1.0"
description = "Portable quality-gate orchestrator for developer tools"
requires-python = ">=3.11,<3.15"
dependencies = [
  "PyYAML>=6.0",
]

[project.scripts]
shipgate = "shipgate.cli:main"

[dependency-groups]
dev = [
  "pytest>=8.0",
  "ruff>=0.6",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]
```

Use `argparse` for the first CLI. It is enough for `install`, `format`, `check`, `list`, and `schema`. A richer CLI library can be added later if the command model proves stable.

## 5. Public CLI behavior

### Commands

Implement these first:

```bash
shipgate
shipgate install
shipgate format
shipgate check
shipgate list suites
shipgate list tools
shipgate list checks
shipgate schema
```

Default command behavior:

- `shipgate` is an alias for `shipgate check`.
- `shipgate check` runs report-only checks.
- `shipgate format` runs apply-capable checks.
- `shipgate install` installs tools required by the selected suite.
- `shipgate list ...` reads catalog metadata only. It should not execute tools.
- `shipgate schema` prints canonical report JSON Schema.

### Shared flags

Add these early:

```text
--config PATH
--suite SUITE_ID
--check CHECK_ID
--target PATH
--error-format FORMAT
--output-dir PATH
--extra-arg VALUE
--verbose
--quiet
```

Do not expose tool-specific flags except through `--extra-arg`.

### Exit codes

Use these rules:

- `0`: command completed and no failing findings were reported
- `1`: command completed and one or more checks failed
- `2`: ShipGate usage or configuration error
- `3`: tool installation or environment error
- `4`: internal ShipGate error

Quiet success means no stdout and no stderr unless `--verbose` is set.

### Failure behavior

On failure:

1. write canonical JSON to `.shipgate/reports/failures/<run-id>/report.json`
1. render the selected `error-format` to stderr
1. exit `1`

If ShipGate itself fails before a tool runs, print a short diagnostic to stderr and exit with the right non-`1` code.

## 6. Domain model files

### `src/shipgate/domain/ids.py`

Define branded string types or small frozen dataclasses for IDs.

Recommended initial shape:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RunnableId:
    value: str

@dataclass(frozen=True)
class SuiteId:
    value: str

@dataclass(frozen=True)
class CheckId:
    value: str

@dataclass(frozen=True)
class CapabilityId:
    value: str
```

Keep validation strict:

- non-empty
- lowercase letters, digits, dot, underscore, and hyphen
- no spaces
- no path separators

Tests:

- accepts `ruff.lint`
- accepts `python-quality`
- rejects empty ID
- rejects `../tool`
- rejects `Ruff Lint`

### `src/shipgate/domain/modes.py`

Define run modes.

```python
from enum import Enum

class RunMode(str, Enum):
    CHECK = "check"
    APPLY = "apply"
    INSTALL = "install"
```

`format` command maps to `RunMode.APPLY`.

### `src/shipgate/domain/options.py`

Define normalized options.

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class NormalizedOptions:
    paths: tuple[Path, ...] = ()
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    config: tuple[Path, ...] = ()
    format: str | None = None
    output: Path | None = None
    verbose: bool | None = None
    quiet: bool | None = None
    fix: bool | None = None
    rules: tuple[str, ...] = ()
    threshold: str | None = None
    stdin: str | None = None
    exit_behavior: str | None = None

@dataclass(frozen=True)
class OptionValue:
    value: object
    source: str
```

`NormalizedOptions` represents values. `OptionValue` is used during planning when source tracking matters.

### `src/shipgate/domain/project.py`

Define project config.

```python
@dataclass(frozen=True)
class ProjectConfig:
    suite: str | None
    env: str
    target: Path
    error_format: str
    config_mode: str
    checks: tuple[str, ...]
    scopes: Mapping[str, Scope]
```

Defaults:

- `suite`: `standard`
- `env`: `managed`
- `target`: `.`
- `error_format`: `json`
- `config_mode`: `auto`
- `checks`: empty tuple
- `scopes`: include target, respect `.gitignore`

### `src/shipgate/domain/catalog.py`

Define catalog objects:

```python
@dataclass(frozen=True)
class ToolDefinition:
    id: str
    executable: str
    subcommand: tuple[str, ...]
    cli: Mapping[str, CliOptionDefinition]
    configuration: ConfigurationDefinition
    capabilities: tuple[str, ...]
    install: InstallDefinition | None
    normalizer: str
    modes: tuple[RunMode, ...]

@dataclass(frozen=True)
class SuiteDefinition:
    id: str
    members: tuple[str, ...]
    parallel: bool
    fail_fast: bool

@dataclass(frozen=True)
class Catalog:
    tools: Mapping[str, ToolDefinition]
    suites: Mapping[str, SuiteDefinition]
```

Use runtime validation when loading YAML. Do not rely on type hints alone.

### `src/shipgate/domain/execution.py`

Define request objects:

```python
@dataclass(frozen=True)
class ExecutionRequest:
    runnable: str
    mode: RunMode
    options: NormalizedOptions
    extra_args: tuple[str, ...]
    project_root: Path

@dataclass(frozen=True)
class ResolvedRequest:
    runnable: str
    tool: ToolDefinition
    mode: RunMode
    options: NormalizedOptions
    option_sources: Mapping[str, str]
    extra_args: tuple[str, ...]
    project_root: Path
    output_path: Path
    environment: ExecutionEnvironment
```

Resolved requests should be immutable. They are the handoff between planning and execution.

### `src/shipgate/domain/reports.py`

Define canonical output:

```python
@dataclass(frozen=True)
class FindingLocation:
    path: str
    line: int | None = None
    column: int | None = None

@dataclass(frozen=True)
class Finding:
    check_id: str
    rule_id: str
    severity: str
    message: str
    location: FindingLocation | None
    report_path: str | None = None
    extra: Mapping[str, object] = field(default_factory=dict)

@dataclass(frozen=True)
class CheckReport:
    check_id: str
    tool_id: str
    status: str
    exit_code: int
    findings: tuple[Finding, ...]
    stdout_path: str | None
    stderr_path: str | None
    extra: Mapping[str, object] = field(default_factory=dict)

@dataclass(frozen=True)
class RunReport:
    run_id: str
    suite: str | None
    mode: str
    status: str
    reports: tuple[CheckReport, ...]
```

Keep canonical schema versioned:

```json
{
  "schema_version": "shipgate.report.v1"
}
```

## 7. Project configuration

### User config file

Start with this minimal `shipgate.yaml`:

```yaml
suite: standard
env: managed
target: .
error-format: compact
configs:
  mode: auto
```

Fields:

- `suite`: default suite for `install`, `format`, and `check`
- `env`: `managed` or `system`
- `target`: repository target path
- `error-format`: `json`, `compact`, `text`, or `github`
- `configs.mode`: `auto`, `repo`, or `bundled`
- Tool configs live under `.shipgate/configs/` (scaffolded by `shipgate init` or `shipgate configs sync`; copy-if-missing only)
- `checks`: optional explicit check IDs
- `scopes`: optional named scopes
- `error-formatters`: optional custom formatters after built-ins work

### `src/shipgate/config/loader.py`

Responsibilities:

- find config path
- parse YAML
- apply defaults
- return `ProjectConfig`
- produce useful config errors

Search order:

1. `--config`
1. `shipgate.yaml`
1. `.shipgate.yaml`
1. no file, use defaults

No config file should still work.

### Tests

Create `tests/unit/config/test_loader.py`.

Required tests:

- missing config returns defaults
- minimal config parses
- unknown top-level key fails with exit-code category `2`
- invalid `env` fails
- invalid `error-format` fails
- CLI `--config` path wins over discovered config

## 8. Catalog format

### Bundled catalog

Start with `src/shipgate/catalog/bundled/catalog.yaml`.

Initial content should include:

- one check-capable tool: `ruff.lint`
- one apply-capable tool: `ruff.format`
- one suite: `python-quality`
- one suite: `format`
- one suite: `standard`

Example:

```yaml
tools:
  ruff.lint:
    executable: ruff
    subcommand: ["check"]
    modes: ["check"]
    capabilities: ["Linting", "Quality"]
    normalizer: ruff
    install:
      manager: python
      package: ruff
      version: ">=0.6"
    cli:
      paths:
        style: positional
      config:
        flag: --config
        style: repeated
      exclude:
        flag: --exclude
        style: repeated
      output:
        flag: --output-file
        style: scalar
      format:
        flag: --output-format
        style: scalar
    configuration:
      bundled: configs/ruff.toml
      discover:
        - .ruff.toml
        - ruff.toml
        - pyproject.toml
      pyproject_section: tool.ruff
      precedence:
        - cli
        - repo
        - bundled
      merge: false

  ruff.format:
    executable: ruff
    subcommand: ["format"]
    modes: ["apply", "check"]
    capabilities: ["Formatting"]
    normalizer: generic_exit
    install:
      manager: python
      package: ruff
      version: ">=0.6"
    cli:
      paths:
        style: positional
      config:
        flag: --config
        style: repeated
      check:
        flag: --check
        style: boolean
    configuration:
      bundled: configs/ruff.toml
      discover:
        - .ruff.toml
        - ruff.toml
        - pyproject.toml
      pyproject_section: tool.ruff
      precedence:
        - cli
        - repo
        - bundled
      merge: false

suites:
  python-quality:
    members:
      - ruff.lint
    parallel: false
    fail_fast: false

  format:
    members:
      - ruff.format
    parallel: false
    fail_fast: true

  standard:
    members:
      - python-quality
    parallel: false
    fail_fast: false
```

This first catalog is deliberately small. Ruff proves the metadata model before the catalog grows.

After the ruff path works, add the initial bundled tool set from the prior ShipGate attempt:

- Ruff for Python linting and formatting
- ty for Python type checking
- Bandit for Python security scanning
- Semgrep for pattern-based security and quality checks
- Gitleaks for secret scanning
- codespell for spelling checks
- deadcode and Vulture for unused Python code detection
- Radon for complexity and maintainability metrics
- pytest for test execution
- mutmut for mutation testing
- pydeps for dependency graphs and import-cycle checks
- markdownlint and mdformat for Markdown checks and formatting
- yamllint and yamlfmt for YAML checks and formatting
- ShellCheck and shfmt for shell script checks and formatting
- Hadolint for Dockerfile linting
- JSCPD for duplicate-code detection
- Sourcery for Python review and refactoring suggestions
- project-local script gates for repository-specific policies

### Catalog validation

`src/shipgate/catalog/validate.py` should validate:

- all IDs are valid
- suite members exist
- suites do not form cycles
- tool modes are valid
- required CLI option definitions are shaped correctly
- normalizer name exists
- bundled config files exist
- install metadata is recognized

Tests:

- valid catalog loads
- missing suite member fails
- cycle fails with readable path
- missing bundled config fails
- unsupported CLI serialization style fails

## 9. Planning layer

Planning is the most important part of ShipGate. Most extensibility failures happen here if the planner starts special-casing tools.

### `planning/workflow.py`

Input:

- command mode
- project config
- requested suite or check override
- catalog

Output:

- ordered runnable IDs

Rules:

- `shipgate check` uses selected project suite unless `--suite` or `--check` is passed
- `shipgate format` uses suite `format` unless the project config says otherwise
- `shipgate install` uses the selected suite and collects install requirements
- `--check` bypasses suite selection and runs exactly one check

Tests:

- default config selects `standard`
- `--suite python-quality` overrides project config
- `--check ruff.lint` runs one tool
- unknown suite fails
- unknown check fails

### `planning/suites.py`

Input:

- suite ID or tool ID
- catalog

Output:

- flattened runnable sequence

Rules:

- tools are leaves
- suites recurse
- cycles fail before execution
- duplicates are removed by default, preserving first occurrence
- duplicate behavior can later become configurable

Tests:

- tool returns itself
- suite expands members
- nested suite expands depth-first
- duplicate leaf appears once
- cycle reports full cycle chain

### `planning/scopes.py`

Input:

- project root
- project config target
- optional named scope
- ignore rules

Output:

- logical scope object, not necessarily a concrete file list

First implementation:

- always respect `.gitignore`
- always ignore `.shipgate/`, `.venv/`, and `.shipgate/reports/`
- support target path
- support explicit include/exclude strings

Do not implement a full gitignore engine by hand. Use one of these approaches:

1. call `git check-ignore` when inside a git repo
1. use a small dependency later if the repo needs full matching
1. initially pass target paths to tools that already respect `.gitignore`

For the first ruff path, prefer passing the project target and let ruff handle file discovery. Scope Resolver still records the policy.

### `planning/defaults.py`

Default option rules:

- `format`: `json` for tool output when supported
- `output`: `.shipgate/reports/raw/<check-id>.json`
- `verbose`: false
- `quiet`: false
- `fix`: true only in apply mode when tool supports mutation
- `paths`: project target if no paths are supplied

Every applied default should record source `shipgate_default`.

### `planning/requests.py`

Build `ExecutionRequest` from CLI/API input, then produce `ResolvedRequest`.

Resolution order:

1. direct CLI/API values
1. project config
1. environment
1. ShipGate defaults
1. tool defaults

The planner must produce an explanation for conflicts:

- `quiet` and `verbose` both true
- `fix` requested in check mode
- apply mode requested for check-only tool
- formatter requested for unsupported output
- `extra_args` conflict with ShipGate-owned option if conflict can be detected

Tests:

- CLI target beats project target
- project suite beats default suite
- default output path is stable
- check mode rejects mutation-only options
- option source map records CLI and defaults

## 10. Adapter layer

### `adapter/serialize.py`

Support these serialization styles:

- `positional`
- `scalar`
- `repeated`
- `joined`
- `boolean`

Behavior:

- positional appends values without flags
- scalar emits `flag value`
- repeated emits `flag value` for every value
- joined emits `flag value1,value2`
- boolean emits flag only when value is true

Tests:

- positional paths serialize after flags unless tool definition says otherwise
- repeated excludes emit multiple flags
- joined excludes use configured separator
- false boolean emits nothing
- unknown option is ignored unless marked required

### `adapter/argv.py`

Input:

- `ResolvedRequest`

Output:

- `tuple[str, ...]`

Algorithm:

1. start with executable
1. append subcommand
1. append config args
1. append normalized option args in catalog-defined order
1. append extra args
1. append positional paths

Catalog order matters. Do not rely on dict order from user config for command stability.

Tests:

- ruff lint command matches expected argv
- ruff format check mode includes `--check`
- extra args are preserved
- paths are last for ruff

## 11. Runtime layer

### `runtime/executor.py`

Define:

```python
@dataclass(frozen=True)
class ProcessResult:
    argv: tuple[str, ...]
    cwd: Path
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    output_files: tuple[Path, ...]
```

Executor behavior:

- run with explicit cwd
- pass explicit environment
- capture stdout and stderr
- enforce timeout
- never parse findings
- return `ProcessResult`

Tests:

- successful command returns exit code 0
- failing command returns non-zero without raising
- timeout returns a controlled ShipGate error
- stdout and stderr are captured

Use fake commands in tests with `python -c` scripts. Do not require ruff for executor unit tests.

### `runtime/reports.py`

Responsibilities:

- create run ID
- create report directories
- write raw stdout and stderr when needed
- write canonical report JSON
- return paths to formatter

Directory layout:

```text
.shipgate/reports/
  raw/
    <run-id>/
      <check-id>/
        stdout.txt
        stderr.txt
        tool-output.json
  failures/
    <run-id>/
      report.json
```

Run ID format:

```text
YYYYMMDDTHHMMSSZ-<short-random>
```

Tests:

- report directories are created
- JSON report is written atomically enough for local use
- paths are relative in canonical report when possible

## 12. Normalizers

### `normalize/base.py`

Define interface:

```python
class Normalizer(Protocol):
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        ...
```

Normalizer registry:

```python
NORMALIZERS: dict[str, Normalizer]
```

Do not load arbitrary Python plugins in the first implementation. Keep registry internal.

### `normalize/ruff.py`

Ruff check JSON maps naturally to findings.

Expected ruff item shape:

```json
{
  "code": "F401",
  "message": "Unused import",
  "filename": "src/main.py",
  "location": {
    "row": 12,
    "column": 5
  }
}
```

Mapping:

- `code` -> `rule_id`
- `message` -> `message`
- `filename` -> `location.path`
- `location.row` -> `location.line`
- `location.column` -> `location.column`
- severity defaults to `error` unless catalog metadata overrides it

Tests:

- empty list gives passed report
- one ruff finding maps all fields
- invalid JSON produces a controlled normalization error
- unknown fields are preserved under `extra.raw`

### `normalize/generic.py`

Generic exit normalizer:

- exit `0` means passed
- non-zero means failed
- stderr becomes one finding if no structured output exists

Use this for early formatters and tools without JSON support.

## 13. Formatters

### Formatter interface

```python
class Formatter(Protocol):
    def render(self, report: RunReport) -> str:
        ...
```

Built-ins:

- `json`
- `compact`
- `text`
- `github`

### `formatters/json.py`

Print pretty JSON.

Rules:

- include `report_path`
- include schema version
- include run status
- include every check report

### `formatters/compact.py`

One finding per line:

```text
src/app.py:42: error: F401 Unused import
```

If location is missing:

```text
ruff.lint: error: TOOL_EXIT Tool failed
```

### `formatters/text.py`

Human-friendly bullet output:

```text
- [error] F401: Unused import (src/app.py:42)
```

### `formatters/github.py`

GitHub annotation format:

```text
::error file=src/app.py,title=ruff.lint/F401,line=42::Unused import
```

Escape `%`, `\r`, `\n`, `:`, and `,` according to GitHub workflow command rules.

Tests:

- json formatter emits valid JSON
- compact formatter handles missing line
- text formatter groups findings by check
- github formatter escapes special characters

## 14. Managed installation

Do not build a package manager. Build a deterministic environment selector for catalog-defined tools.

### `runtime/environment.py`

Define:

```python
@dataclass(frozen=True)
class ExecutionEnvironment:
    kind: str
    root: Path | None
    env: Mapping[str, str]
```

Supported initial modes:

- `system`: use tool on `PATH`
- `managed`: use `.shipgate/tools`

### `runtime/install.py`

Initial Python-tool strategy:

- create one virtual environment under `.shipgate/tools/python`
- install Python packages needed by selected suite
- use `python -m pip install`
- write a lock-like manifest at `.shipgate/tools/manifest.json`

Manifest fields:

```json
{
  "schema_version": "shipgate.install.v1",
  "python": "3.12.3",
  "packages": {
    "ruff": "0.6.9"
  }
}
```

First version can install version ranges. A later version should pin exact resolved versions in the manifest.

Rules:

- `shipgate install` installs all tools for selected suite
- `shipgate check` may auto-install only if project config allows it
- default should be explicit install first, then run
- missing tool in managed env should produce a clear install hint

Tests:

- install planner collects unique packages from suite
- system env does not create `.shipgate/tools`
- managed env resolves executable path inside env
- missing executable produces actionable error

## 15. CLI orchestration

### `cli.py`

The CLI should do orchestration only.

Flow for `shipgate check`:

1. parse args
1. load project config
1. load bundled catalog
1. build Execution Request
1. resolve workflow and suites
1. build Resolved Requests
1. build argv for each request
1. execute each request
1. normalize each result
1. aggregate RunReport
1. write report if failed
1. render selected formatter if failed or verbose
1. exit with mapped code

The CLI should not:

- inspect catalog YAML manually
- serialize argv directly
- parse tool output directly
- decide which findings are errors

Tests:

- `shipgate list suites` prints bundled suites
- `shipgate check --check ruff.lint` wires planner path with fake executor
- quiet success prints nothing
- failing report prints compact output and exits `1`
- invalid config exits `2`

Use dependency injection for tests. CLI should accept an `Application` object or services object so tests can provide fake executor/installer.

## 16. Application service

Add `src/shipgate/app.py`.

This is the top-level use-case layer.

```python
class ShipGateApp:
    def install(self, command: InstallCommand) -> int: ...
    def check(self, command: RunCommand) -> int: ...
    def format(self, command: RunCommand) -> int: ...
    def list_suites(self) -> str: ...
    def list_tools(self) -> str: ...
    def list_checks(self) -> str: ...
    def schema(self) -> str: ...
```

CLI maps parsed args to command objects. `ShipGateApp` coordinates services.

This keeps `cli.py` thin and gives tests a clean target.

## 17. Error model

Create `src/shipgate/errors.py`.

Base exception:

```python
class ShipGateError(Exception):
    exit_code = 4
    title = "internal error"
```

Specialized errors:

- `UsageError`, exit `2`
- `ConfigError`, exit `2`
- `CatalogError`, exit `2`
- `PlanningError`, exit `2`
- `InstallError`, exit `3`
- `ExecutionError`, exit `3`
- `NormalizationError`, exit `4`

Each error should include:

- short message
- optional hint
- optional path

Example:

```text
shipgate: config error: unknown suite "strict"
hint: run "shipgate list suites" to see bundled suites
```

Do not print tracebacks unless `--verbose` is set.

## 18. First vertical slice

The first slice should support this exact user flow:

```bash
pip install -e .
shipgate list suites
shipgate install
shipgate check --check ruff.lint --target sample_files/python
```

Expected behavior:

- `list suites` prints `standard`, `python-quality`, and `format`
- `install` installs ruff into the managed environment
- `check` runs ruff check
- success is quiet and exits `0`
- failure exits `1`
- failure writes `.shipgate/reports/failures/<run-id>/report.json`
- failure prints configured `error-format`

Use fixture files under:

```text
tests/fixtures/python_clean/
tests/fixtures/python_ruff_failure/
```

`python_clean/app.py`:

```python
def main() -> None:
    print("hello")
```

`python_ruff_failure/app.py`:

```python
import os

def main() -> None:
    print("hello")
```

Ruff should report unused import `F401` for the second fixture.

## 19. Test strategy

### Unit tests

Unit tests should cover:

- ID validation
- config parsing
- catalog loading
- catalog validation
- suite expansion
- option precedence
- request resolution
- argv serialization
- report schema serialization
- normalizers
- formatters

Unit tests should not require external tools.

### Integration tests

Integration tests may require ruff.

Mark them:

```python
pytestmark = pytest.mark.integration
```

Integration tests:

- install managed ruff
- run ruff against clean fixture
- run ruff against failing fixture
- verify report JSON
- verify compact output

### CLI tests

Use subprocess only for a small number of end-to-end tests.

Most CLI tests should call `main(argv)` or `ShipGateApp` directly with fakes.

### Golden reports

Store expected canonical reports as JSON fixtures when the schema stabilizes.

Avoid brittle timestamps by normalizing `run_id` in test assertions.

## 20. Milestones

### Milestone 1: package and CLI shell

Deliverables:

- package imports
- console script works
- `shipgate --help`
- `shipgate list suites` from hardcoded in-memory catalog

Tests:

- CLI help exits `0`
- package has version
- list suites prints expected values

### Milestone 2: config and bundled catalog

Deliverables:

- YAML project config loader
- bundled catalog loader
- catalog validation
- default config when file missing

Tests:

- config defaulting
- invalid config errors
- catalog cycle detection
- bundled config file existence

### Milestone 3: planning

Deliverables:

- workflow selection
- suite expansion
- execution request creation
- resolved request creation
- option source tracking

Tests:

- selected suite resolves to ruff
- default output paths
- apply/check mode validation
- CLI overrides config

### Milestone 4: adapter and executor

Deliverables:

- stable argv builder
- process executor
- fake executor support for app tests

Tests:

- expected ruff argv
- executor captures stdout/stderr
- non-zero result does not throw

### Milestone 5: reporting

Deliverables:

- canonical report schema
- ruff normalizer
- generic exit normalizer
- JSON formatter
- compact formatter
- failure report writer

Tests:

- ruff JSON maps to findings
- compact output matches expected line
- JSON report validates against schema

### Milestone 6: managed install

Deliverables:

- managed Python tool environment
- install planner
- `shipgate install`
- executable resolution from managed env

Tests:

- install plan deduplicates packages
- managed executable path used
- missing install gives hint

### Milestone 7: end-to-end ruff suite

Deliverables:

- `shipgate install`
- `shipgate check`
- `shipgate format`
- `standard`, `python-quality`, and `format` suites

Tests:

- clean fixture passes silently
- failing fixture exits `1`
- format applies changes in apply mode
- check mode does not mutate files

### Milestone 8: more bundled tools

Add tools one by one:

1. `ty.check`
1. `bandit.scan`
1. `codespell.check`
1. `gitleaks.scan`
1. `semgrep.scan`
1. `deadcode.check`
1. `vulture.check`
1. `radon.cc`
1. `radon.mi`
1. `pytest.run`
1. `pydeps.graph`
1. `markdownlint.check`
1. `mdformat.apply`
1. `yamllint.check`
1. `yamlfmt.apply`
1. `shellcheck.check`
1. `shfmt.apply`
1. `hadolint.check`
1. `jscpd.check`
1. `mutmut.run`
1. `sourcery.review`
1. `gate.script`

Each tool requires:

- Tool Definition
- bundled config
- normalizer or generic mapping
- unit tests for argv
- integration test when the tool is practical to install in CI

No tool should require changes to planner or executor.

Add risky or slow tools later in the milestone, not first. `mutmut`, `pydeps`, `jscpd`, and `sourcery` need careful defaults because they can be slow, noisy, or service-dependent. They belong in `extended` or explicit suites before they belong in `standard`.

## 21. Detailed task list

### Task 1: create package skeleton

Files:

- create `pyproject.toml`
- create `src/shipgate/__init__.py`
- create `src/shipgate/__main__.py`
- create `src/shipgate/cli.py`
- create `tests/unit/test_import.py`

Steps:

1. Write import test.
1. Add package files.
1. Add CLI returning help text.
1. Run `pytest`.
1. Run `python -m shipgate --help`.

Success:

- tests pass
- CLI imports
- no external tools required

### Task 2: add domain models

Files:

- create `src/shipgate/domain/ids.py`
- create `src/shipgate/domain/modes.py`
- create `src/shipgate/domain/options.py`
- create `src/shipgate/domain/project.py`
- create `src/shipgate/domain/catalog.py`
- create `src/shipgate/domain/execution.py`
- create `src/shipgate/domain/reports.py`
- create matching unit tests

Success:

- ID validation works
- dataclasses are immutable where needed
- tests do not touch filesystem except path values

### Task 3: load project config

Files:

- create `src/shipgate/config/loader.py`
- create `src/shipgate/config/schema.py`
- create `tests/unit/config/test_loader.py`

Success:

- no config file gives default `ProjectConfig`
- minimal YAML parses
- invalid YAML gives `ConfigError`
- unknown key gives `ConfigError`

### Task 4: load bundled catalog

Files:

- create `src/shipgate/catalog/bundled/catalog.yaml`
- create `src/shipgate/catalog/bundled/configs/ruff.toml`
- create `src/shipgate/catalog/loader.py`
- create `src/shipgate/catalog/validate.py`
- create `tests/unit/catalog/test_loader.py`
- create `tests/unit/catalog/test_validate.py`

Success:

- bundled catalog loads from package resources
- catalog validates suite references
- catalog detects cycles

### Task 5: implement suite and workflow planning

Files:

- create `src/shipgate/planning/workflow.py`
- create `src/shipgate/planning/suites.py`
- create `tests/unit/planning/test_workflow.py`
- create `tests/unit/planning/test_suites.py`

Success:

- default workflow resolves to `standard`
- nested suite expands to tool IDs
- duplicate leaves dedupe
- cycles fail

### Task 6: implement request resolution

Files:

- create `src/shipgate/planning/requests.py`
- create `src/shipgate/planning/defaults.py`
- create `tests/unit/planning/test_requests.py`

Success:

- Execution Request contains only user-supplied options
- Resolved Request contains defaults
- option source map records precedence
- invalid mode/tool combinations fail

### Task 7: implement adapter

Files:

- create `src/shipgate/adapter/serialize.py`
- create `src/shipgate/adapter/argv.py`
- create `tests/unit/adapter/test_serialize.py`
- create `tests/unit/adapter/test_argv.py`

Success:

- ruff argv is deterministic
- serialization styles work
- unknown style fails during catalog validation, not at execution time

### Task 8: implement executor

Files:

- create `src/shipgate/runtime/executor.py`
- create `tests/unit/runtime/test_executor.py`

Success:

- executor captures process output
- non-zero exit is returned as data
- timeout is controlled

### Task 9: implement reporting and normalization

Files:

- create `src/shipgate/normalize/base.py`
- create `src/shipgate/normalize/ruff.py`
- create `src/shipgate/normalize/generic.py`
- create `src/shipgate/runtime/reports.py`
- create `tests/unit/normalize/test_ruff.py`
- create `tests/unit/runtime/test_reports.py`

Success:

- ruff JSON maps to canonical report
- report writer writes `report.json`
- schema version appears in output

### Task 10: implement formatters

Files:

- create `src/shipgate/formatters/json.py`
- create `src/shipgate/formatters/compact.py`
- create `src/shipgate/formatters/text.py`
- create `src/shipgate/formatters/github.py`
- create formatter tests

Success:

- compact output matches expected format
- GitHub output escapes special characters
- JSON output is parseable

### Task 11: implement application service and CLI wiring

Files:

- create `src/shipgate/app.py`
- update `src/shipgate/cli.py`
- create `tests/unit/test_app.py`
- create `tests/unit/test_cli.py`

Success:

- quiet success produces no output
- failure prints selected formatter
- invalid config exits `2`
- `list suites`, `list tools`, and `list checks` work

### Task 12: implement managed install

Files:

- create `src/shipgate/runtime/environment.py`
- create `src/shipgate/runtime/install.py`
- create `tests/unit/runtime/test_install.py`

Success:

- install requirements collected from selected suite
- manifest written
- managed executable resolution works
- system env skips managed install

### Task 13: add end-to-end ruff integration

Files:

- create `tests/fixtures/python_clean/app.py`
- create `tests/fixtures/python_ruff_failure/app.py`
- create `tests/integration/test_ruff_e2e.py`

Success:

- clean fixture passes
- failing fixture exits `1`
- report contains `F401`
- compact output contains file, line, severity, rule, and message

## 22. Decisions to settle during implementation

Do not block Milestone 1 on these. Close them before adding many tools.

### Config schema strictness

Recommendation: strict top-level keys, lenient nested catalog metadata only where extension requires it.

Why: users should find typos early.

### Manifest locking

Recommendation: first version writes observed versions after install. Later version supports a lock command.

Why: deterministic installs matter, but exact resolver behavior can wait until managed install works.

### Parallel execution

Recommendation: keep execution sequential until report aggregation, cancellation, and logging are stable.

Why: parallelism makes failure behavior harder to reason about.

### Plugin API

Recommendation: no public plugin API in v1.

Why: catalog schema and normalizer contract need real use before becoming public compatibility promises.

### Report frontend

Recommendation: build a local SonarQube-inspired frontend after canonical reports, report storage, and CLI failure behavior are stable.

Why: the frontend should read ShipGate reports, not raw tool output. Building it too early would freeze the report model before the CLI has proven it.

## 23. Acceptance criteria

The first releasable version is acceptable when:

- `shipgate install` installs tools for the selected suite
- `shipgate check` runs report-only checks
- `shipgate format` runs apply checks
- no config file still gives a useful default suite
- success is quiet and exits `0`
- failures write canonical JSON and print selected formatter output
- at least ruff lint and ruff format work through catalog metadata
- adding a second tool does not require planner, adapter, executor, or formatter changes
- unit tests cover config, catalog, planning, adapter, normalization, and formatting
- integration tests prove one real tool path

## 24. What not to build first

Do not build these in the first slice:

- report frontend
- public plugin loading
- remote execution
- distributed execution
- result caching
- baseline comparison
- custom formatter scripting
- project-local gates
- dashboard UI beyond the report frontend

Each is useful, but each depends on stable reports, stable catalog metadata, and stable execution semantics.

## 25. Implementation rule of thumb

When adding any feature, ask one question:

Does this belong in project policy, catalog metadata, request planning, process execution, normalization, or formatting?

If the answer is unclear, do not add the feature yet. ShipGate becomes hard to extend when those boundaries blur.
