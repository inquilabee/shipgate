# ShipGate software design document

**Version:** 1.0  
**Status:** Draft  
**Audience:** framework maintainers, catalog authors, plugin developers

**Implementation guide:** `docs/implementation.md`

## 1. Vision

ShipGate is a repository automation framework for developer tools.

It gives projects a consistent way to run formatting, linting, typing, security scanning, documentation validation, and organization-specific checks without exposing every tool's command line, configuration format, and output shape.

The product boundary is important:

- Projects describe what should happen.
- ShipGate decides how to invoke tools.
- Tools still do the underlying work.

ShipGate is repo-policy-first. The normalized execution model is the engine underneath that policy layer, not a separate product that tries to replace every tool CLI.

### Product inspirations

ShipGate is inspired by three existing tool categories:

- Trunk Code Quality, especially the idea that a repository should become useful almost immediately after installation.
- pre-commit, especially the idea of running repeatable checks at developer workflow boundaries.
- SonarQube, especially the idea of aggregating code-quality signals into a consistent reporting model and making them browsable in a frontend.

ShipGate should feel ready by default. A conventional repository should be able to install ShipGate, run a default workflow, and get useful results without first writing a large configuration file.

### Prior attempt

An earlier implementation attempt exists at `inquilabee/shipgate`. It was a useful product sketch: one project config, bundled checks, managed installs, quiet success, structured failure reports, a small command set such as `shipgate install`, `shipgate format`, and `shipgate check`, and a frontend inspired by SonarQube.

That attempt is considered not extensible enough for the long-term design. The core goals remain the same, but this design changes the internals:

- tool behavior moves into declarative Tool Definitions
- invocations flow through Execution Requests
- suites become recursive runnables
- output passes through normalizers before formatting
- catalog entries become the main extension point

The lesson is not to discard the earlier UX. The lesson is to keep that UX while making the execution model metadata-driven.

The frontend remains part of the product direction. It should be built on canonical ShipGate reports, not on raw tool output. The CLI and report schema come first; the frontend comes after those contracts are stable.

## 2. Design goals

### Declarative

Projects declare policy and intent. They do not describe subprocess behavior, argument ordering, recursive traversal, or installation paths.

### Ready by default

ShipGate ships opinionated catalogs, bundled tool configurations, default suites, and default workflows.

Configuration is for overriding policy, not for making the product usable for the first time.

The ShipGate repository should dogfood those defaults. Its own standard Python suite should be a proof that the bundled defaults are strong enough for serious Python development, not merely a loose starter preset.

### Predictable

The same project configuration, catalog version, and runtime version should produce the same resolved execution plan.

### Extensible

Adding support for a new tool should primarily require metadata, bundled configuration, and an output normalizer. The planner, adapter, executor, and formatters should rarely change.

### Repository agnostic

ShipGate should not assume a language, build system, package manager, or repository layout.

### Composable

Individual tools can be grouped into suites and workflows without changing how leaf tools execute.

### Stable

Project configuration should describe long-lived concepts. Execution details stay in the runtime and catalog so tool behavior can change without forcing config churn.

## 3. Core principles

### Policy stays separate from execution

Project configuration expresses intent. The runtime and catalog handle execution.

Project config must not expose:

- command-line flags
- recursion flags
- argument templates
- subprocess options
- installation locations
- output-file conventions

Those are framework concerns.

### Everything executable is a runnable

ShipGate has one execution abstraction: a runnable.

There are two runnable kinds:

- A tool executes one external executable.
- A suite executes one or more runnables.

This gives ShipGate a recursive model. The runtime can execute `ruff-check`, `quality`, `security`, or `ci` through the same lifecycle.

### Execution Request is the internal API

The CLI is not the core API. The Execution Request is.

Every front end produces an Execution Request:

- CLI commands
- Python API calls
- YAML batch files
- CI integrations
- future UI integrations

Everything after that point uses the same pipeline.

### Infrastructure adapts to the domain

The core domain must not depend on subprocess APIs, filesystem implementations, package managers, operating systems, or environment variables.

Infrastructure code adapts those concerns into the domain model.

## 4. Conceptual model

ShipGate has three layers.

```text
Repository policy
  -> Workflow / Check / Scope
  -> Execution Request
  -> Resolved Request
  -> Tool Definition
  -> CLI Adapter
  -> Executor
  -> Normalizer
  -> Formatter
```

The top layer answers "what should run for this repository?"

The middle layer answers "what exactly are we asking ShipGate to execute?"

The lower layer answers "how do we call the tool and turn its output into ShipGate output?"

## 5. Domain model

### Scope

A scope defines where checks apply.

A scope contains:

- include rules
- exclude rules
- optional filters

A scope does not describe recursion, command-line arguments, delivery strategy, or tool behavior.

Example:

```yaml
scopes:
  source:
    include:
      - src/
      - tests/

  documentation:
    include:
      - docs/
      - README.md
```

### Check

A check represents one executable unit of validation or mutation.

Examples:

- formatting
- linting
- typing
- security
- documentation
- architecture
- custom organization policy

Example:

```yaml
checks:
  bandit.scan:
    scope: source

  ty.check:
    scope: source
```

A check binds repository policy to a catalog entry. It does not define command flags or tool invocation.

### Workflow

A workflow defines an ordered sequence of checks or capabilities for a user intent such as `default`, `ci`, `release`, `pre-commit`, or `nightly`.

Example:

```yaml
workflows:
  default:
    - apply:
        - formatting
    - check:
        - quality
```

`apply` means the runnable may modify files. `check` means it should report results without mutating the repository. Tools that cannot honor the requested mode must fail during planning.

### Capability

Capabilities classify checks by user intent, independent of implementation.

Examples:

- Formatting
- Linting
- Typing
- Security
- Secrets
- Documentation
- Architecture
- Testing

Capabilities are semantic. They should not describe execution details.

### Catalog

The catalog is ShipGate's knowledge base.

It defines:

- tool definitions
- suite definitions
- capabilities
- supported normalized options
- configuration discovery
- bundled configuration
- installation metadata
- output normalization metadata or normalizer bindings
- defaults

Projects reference catalog entries but do not redefine them.

### Initial bundled tool set

The initial catalog should start from the tool set proven useful in the prior ShipGate attempt.

Start with these tools:

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

Ruff should be the first vertical-slice tool because it can prove linting, formatting, configuration discovery, output normalization, and managed installation with one dependency. The broader catalog should be added only after the ruff path proves the metadata model.

### Tool Definition

A Tool Definition describes how a tool behaves and how ShipGate serializes a resolved request into argv.

Example:

```yaml
id: ruff-check

tool:
  executable: ruff
  subcommand:
    - check
  extra_args:
    defaults:
      - --preview

cli:
  paths:
    cli_style: positional

  config:
    flag: --config

  exclude:
    flag: --exclude
    cli_style: joined
    separator: ","

configuration:
  bundled: ruff.toml
  discover:
    - .ruff.toml
    - ruff.toml
    - pyproject.toml
  pyproject:
    section: tool.ruff
  precedence:
    - cli
    - .ruff.toml
    - ruff.toml
    - pyproject.toml
    - bundled
  merge: false

capabilities:
  - Linting
```

The Tool Definition contains metadata, not executable tool-specific branching.

### Suite Definition

A suite is a runnable made from other runnables.

Example:

```yaml
name: quality

members:
  - ruff-check
  - ty-check
  - deadcode
  - radon-cc
  - radon-mi

parallel: true
fail_fast: false
```

Suites may contain tools or other suites. Suite expansion must detect cycles and duplicate execution before running anything.

## 6. Normalized invocation

Users may invoke ShipGate directly:

```bash
shipgate ruff-check src tests --exclude build --config pyproject.toml --fix
```

The CLI parser must not build tool argv directly. It produces an Execution Request.

```yaml
runnable: ruff-check

options:
  paths:
    - src
    - tests
  exclude:
    - build
  config:
    - pyproject.toml
  fix: true

extra_args: []
```

The request is tool-independent. Ruff-specific flags appear only after planning and adapter serialization.

## 7. Execution Request

The Execution Request is the central object in ShipGate.

Everything before it is user interface. Everything after it is execution.

Normalized options should stay small and portable:

- paths
- include
- exclude
- config
- format
- output
- verbose
- quiet
- fix
- rules
- threshold
- stdin
- exit_behavior

Unsupported tool-specific arguments use `extra_args`.

Example:

```yaml
runnable: ruff-check

options:
  paths:
    - src
    - tests
  exclude:
    - build
  config:
    - pyproject.toml
  format: json
  output: ruff-check.json
  fix: true

extra_args:
  - --preview
```

ShipGate owns normalized options. `extra_args` is an escape hatch, not the normal extension path.

## 8. Option sources and precedence

The initial request should contain only what the user supplied.

The planner produces a Resolved Request by applying defaults and configuration sources.

Precedence order:

1. CLI or direct API request
2. Project configuration
3. Environment
4. ShipGate defaults
5. Tool defaults

Every resolved option should retain its source. That makes diagnostics clearer and prevents silent surprises.

Example default behavior:

```yaml
options:
  format: json
  output: ruff-check.json
  verbose: false
  quiet: false
```

## 9. Execution pipeline

```text
User
  -> CLI / API / batch file
  -> Execution Request
  -> Workflow Planner
  -> Check Planner
  -> Scope Resolver
  -> Execution Planner
  -> Resolved Request
  -> Tool Definition
  -> CLI Adapter
  -> Executor
  -> Tool output
  -> Normalizer
  -> Canonical ShipGate JSON
  -> Formatter
  -> Final output
```

### Workflow Planner

The Workflow Planner resolves workflow names into ordered work.

It owns:

- workflow expansion
- execution ordering
- dependency validation
- suite references from workflows

### Check Planner

The Check Planner resolves project checks into runnable execution units.

It owns:

- capability resolution
- catalog lookup
- check defaults
- project overrides
- validation of `apply` versus `check`

### Scope Resolver

The Scope Resolver turns repository policy into logical scopes.

It owns:

- include rules
- exclude rules
- ignore rules
- repository awareness

It does not build command-line arguments. Scope resolution should stay lazy until the selected execution strategy needs concrete paths.

### Execution Planner

The Execution Planner converts requested work into Resolved Requests.

It owns:

- applying defaults
- resolving configuration files
- selecting bundled configuration
- validating normalized options
- merging configuration sources
- determining output filenames
- determining output formats
- expanding suites
- detecting cyclic runnable graphs

### CLI Adapter

The CLI Adapter converts a Resolved Request and Tool Definition into argv.

Input:

- Tool Definition
- Resolved Request

Output:

```text
ruff
check
--config
pyproject.toml
--exclude
build,.venv
--output-format
json
src
tests
```

The adapter supports a small set of serialization strategies:

- positional
- repeated flag
- joined flag with configurable separator

The adapter should not parse CLI flags or interpret tool results.

### Executor

The Executor runs a process.

It owns:

- process invocation
- timeout
- environment preparation
- stdout capture
- stderr capture
- exit code capture
- output-file collection

It does not interpret results.

### Normalizer

The Normalizer converts tool output into canonical ShipGate JSON.

Example:

```json
{
  "tool": "ruff-check",
  "summary": {
    "errors": 1,
    "warnings": 4
  },
  "issues": [
    {
      "rule": "F401",
      "severity": "warning",
      "message": "Unused import",
      "location": {
        "path": "src/main.py",
        "line": 12,
        "column": 5
      },
      "extra": {}
    }
  ]
}
```

The `extra` object preserves tool-specific details that do not fit the common schema.

### Formatter

Formatters render canonical ShipGate JSON.

Supported formatter targets may include:

- JSON
- console
- Markdown
- HTML
- SARIF
- JUnit
- CI annotations

Formatters must not consume raw tool-specific output.

## 10. Suite execution

Running a suite expands it into leaf runnables.

Example:

```text
quality
  -> ruff-check
  -> ty-check
  -> deadcode
  -> radon-cc
  -> radon-mi
```

Nested suites use the same model.

```text
ci
  -> python
      -> quality
      -> security
      -> testing
  -> documentation
      -> markdownlint
      -> mdformat
```

Suite execution must define:

- ordering
- parallelism
- fail-fast behavior
- cancellation behavior
- duplicate runnable handling
- cycle detection
- summary aggregation

Because each tool produces canonical ShipGate JSON, suite output is aggregation.

```json
{
  "suite": "quality",
  "summary": {
    "tools": 5,
    "errors": 12,
    "warnings": 37
  },
  "tools": []
}
```

## 11. Configuration discovery

Tool Definitions describe configuration discovery.

For example:

```text
.ruff.toml
  -> ruff.toml
  -> pyproject.toml
  -> ShipGate bundled configuration
```

The planner owns discovery and precedence. The adapter only receives the resolved configuration path or generated config path.

Bundled configurations live with the catalog and give ShipGate opinionated defaults.

Example:

```text
configs/
  ruff.toml
  bandit.yaml
  semgrep.yaml
  shellcheckrc
  yamllint.yaml
```

If a project provides no configuration, ShipGate should use bundled configuration whenever the selected tool supports it.

The first-run path should be useful without project-specific setup:

```bash
shipgate
shipgate ci
shipgate quality
```

Those commands should resolve through default workflows and suites supplied by the catalog. Projects can then override scopes, checks, suites, or configuration discovery when the defaults are not enough.

## 12. Installation model

ShipGate manages tool installations.

The installation model should be:

- isolated
- reproducible
- version pinned
- deterministic
- cacheable

The catalog defines install metadata. The runtime creates and selects execution environments.

The design still needs exact rules for:

- environment location
- cache keys
- invalidation
- lockfiles
- offline behavior
- per-tool versus shared environments

## 13. Extension model

Supporting a new tool should usually require:

1. Tool Definition
2. Bundled configuration
3. Output Normalizer
4. Optional installer metadata

The execution engine, planner, adapter, executor, and formatters should not need tool-specific branches.

Custom suites and organization policy packs can be catalog additions.

Public plugin APIs should wait until the internal catalog and normalizer contracts are stable.

## 14. Non-goals

ShipGate is not:

- a package manager
- a build system
- a CI platform
- a general task runner
- a workflow engine
- a language server

ShipGate's job ends at repository quality orchestration and normalized developer-tool execution.

## 15. Architectural constraints

### Projects must not configure execution mechanics

Configuration should never expose concepts such as argument templates, delivery modes, recursion flags, target expansion, subprocess options, or formatter internals.

### Runtime layers remain independent

Each component owns one responsibility.

Examples:

- Scope resolution does not execute tools.
- Reporting does not understand project configuration.
- Command construction does not traverse repositories.
- The executor does not normalize results.

### Capabilities remain semantic

Capabilities represent user intent, such as Security, Formatting, or Typing. They do not represent command flags, execution strategies, or file traversal behavior.

### Normalized options stay small

The normalized CLI must not grow until it becomes every tool's CLI under new names. If only one tool needs an option, prefer catalog metadata or `extra_args`.

## 16. Future evolution

The architecture can support:

- plugin catalogs
- organization policy packs
- distributed execution
- remote runners
- execution caching
- incremental analysis
- baseline comparison
- git-aware execution
- SonarQube-inspired local report frontend
- custom formatters

These should be infrastructure or catalog improvements, not project-configuration churn.

## 17. Open decisions

The design is coherent enough to implement a small vertical slice, but these decisions should be closed before broad implementation:

- exact project configuration schema
- exact catalog schema
- capability-to-check resolution rules
- override and merge behavior
- suite cycle and duplicate handling
- failure semantics for sequential and parallel execution
- installation cache and lockfile model
- canonical JSON schema versioning
- normalizer contract
- formatter contract

The first implementation slice should prove one path end to end:

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
  -> JSON formatter
```
