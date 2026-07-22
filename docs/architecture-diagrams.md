# ShipGate architecture diagrams

Visual companion to `docs/sdd.md` and `docs/implementation.md`. Diagrams reflect the current codebase, not planned features.

## High level — system context

ShipGate sits between repository policy and external quality tools. Projects declare intent in `shipgate.yaml`; ShipGate loads bundled catalog metadata, plans runs, executes tools, and produces canonical reports.

```mermaid
flowchart TB
    subgraph users["Users and automation"]
        Dev["Developer"]
        CI["CI / pre-commit"]
    end

    subgraph entry["Entry points"]
        CLI["cli.py"]
        API["api.py — Python API"]
        Batch["batch files"]
        Serve["shipgate serve — frontend"]
    end

    subgraph shipgate["ShipGate core"]
        App["app.py — ShipGateApp"]
        Session["RunSession / CheckRunner"]
    end

    subgraph policy["Repository policy"]
        YAML["shipgate.yaml"]
        Configs[".shipgate/configs/"]
        LocalGates[".shipgate/gates/*.sh"]
    end

    subgraph catalog["Catalog metadata"]
        Bundled["catalog/bundled/catalog/"]
        GateMerge["gates/catalog.py — merge local gates"]
    end

    subgraph external["External executables"]
        Tools["Bundled tools — ruff, semgrep, bandit, …"]
        GateScripts["Gate scripts — bash + lib.sh"]
        PolicyPy["policy/ — Python helpers for bundled gates"]
    end

    subgraph output["Reports and UI"]
        Reports[".shipgate/reports/"]
        Store["ReportStore"]
        Frontend["frontend/ — FastAPI + SQLite"]
    end

    Dev --> CLI
    Dev --> Serve
    CI --> CLI
    CI --> API

    CLI --> App
    API --> App
    Batch --> App
    Serve --> App
    Serve --> Frontend

    App --> YAML
    App --> Bundled
    App --> GateMerge
    GateMerge --> LocalGates
    App --> Session

    Session --> Tools
    Session --> GateScripts
    GateScripts --> PolicyPy

    Session --> Reports
    Session --> Store
    Frontend --> Store
    Frontend --> Reports
    Configs -.-> Session
```

Developers and CI invoke ShipGate through the CLI, Python API, or batch files. `ShipGateApp` loads project config and catalog metadata (including discovered local gates), then delegates suite runs to `RunSession`. External tools and gate scripts perform the actual checks; results land in `.shipgate/reports/` and can be browsed via `shipgate serve`.

## Mid level — layer flow for `check` / `format`

A `check` or `format` run follows the same pipeline; only `RunMode` (`check` vs `apply`) and which catalog tools participate differ. Layers are one responsibility each — see `.cursor/rules/architecture.mdc`.

```mermaid
flowchart LR
    subgraph entry_layer["Entry"]
        CLI2["cli.py"]
        App2["app.py"]
    end

    subgraph domain_layer["domain/"]
        Types["ProjectConfig, Catalog, ExecutionRequest, ResolvedRequest, CheckReport, RunReport"]
    end

    subgraph load_layer["Config and catalog"]
        Config["config/ — discovery, loader, schema"]
        Catalog["catalog/ — loader, validate, bundled YAML"]
        GatesCat["gates/catalog.py — merge .shipgate/gates"]
    end

    subgraph plan_layer["planning/"]
        Workflow["workflow.py — suites, workflows, PlannedCheck"]
        Scopes["scopes.py + scope_resolver.py + gitignore.py"]
        Requests["requests.py — build_execution_request, resolve_request"]
        Incremental["incremental.py — changed-only / since"]
    end

    subgraph adapt_layer["adapter/"]
        Argv["argv.py + serialize.py — CliSerializer"]
        ConfigResolve["config_resolve.py — tool config paths"]
    end

    subgraph run_layer["runtime/"]
        Context["session/context.py — prepare_context"]
        Planner["session/check_planner.py — PreparedCheck"]
        Runner["session/check_runner.py — execute + normalize"]
        Exec["executor.py — subprocess"]
        Env["environment.py — managed venv, PATH"]
        RawReports["reports.py — raw stdout/stderr"]
        Store["report_store.py — final RunReport history"]
        Finalizer["session/finalizer.py — format + save_final"]
    end

    subgraph norm_layer["normalize/"]
        Norm["tool normalizers — ruff, semgrep, gate_json, …"]
    end

    subgraph fmt_layer["formatters/"]
        Fmt["compact, json, text, github"]
    end

    CLI2 --> App2
    App2 --> Config
    App2 --> Catalog
    App2 --> GatesCat
    App2 --> Context

    Config --> Types
    Catalog --> Types
    GatesCat --> Catalog

    Context --> Workflow
    Context --> Env

    Runner --> Planner
    Planner --> Scopes
    Planner --> Incremental
    Planner --> Requests
    Planner --> ConfigResolve
    Runner --> Argv
    Runner --> Exec
    Runner --> Norm
    Runner --> RawReports
    Finalizer --> Store
    Finalizer --> Fmt

    Requests --> Types
    Argv --> Types
    Norm --> Types
```

`cli.py` parses flags into `RunCommand` and calls `ShipGateApp.check` or `.format`. `prepare_context` loads config, resolves the suite or workflow into `PlannedCheck` items, and builds the execution environment. `CheckRequestPlanner` converts each planned check into a skipped `CheckReport` or a `ResolvedRequest`; `CheckRunner` executes argv, writes raw output, and normalizes results. Finalizers persist history through `ReportStore.save_final` and format failures via `formatters/` (successes stay quiet unless `--verbose`).

### Gates and policy (cross-cutting)

```mermaid
flowchart TB
    subgraph bundled_gates["Bundled gates — policy suite"]
        BGScripts["catalog/bundled/gates/*.sh"]
        BGConfig["catalog/bundled/configs/gates/"]
        Policy["policy/ — acronym_allowlist, folder_breadth"]
    end

    subgraph local_gates["Project gates — local-gates suite"]
        LGScripts[".shipgate/gates/*.sh"]
        LibSh["gates/lib.sh helpers"]
    end

  subgraph gate_runtime["gates/ runtime"]
        GRuntime["gates/runtime.py — prepare_gate_execution"]
        GInit["gates/init.py — scaffold scripts"]
    end

    BGScripts --> GRuntime
    LGScripts --> GRuntime
    BGScripts --> Policy
    GRuntime --> LibSh
    GRuntime --> BGConfig
```

Bundled policy gates are shell scripts backed by Python helpers in `policy/`. Project-local gates under `.shipgate/gates/` are discovered at runtime and merged into the catalog as `gate.<name>` tools in the `local-gates` suite. Both paths use `gates/runtime.py` to set `SHIPGATE_*` environment variables and emit JSON for the `gate_json` normalizer.

## Detailed — single check execution

Sequence for one `PlannedCheck` inside `prepare_check` → `execute_check` (`runtime/session/check_planner.py`, `check_runner.py`).

```mermaid
sequenceDiagram
    actor User
    participant CLI as cli.py
    participant App as ShipGateApp
    participant Ctx as prepare_context
    participant Planner as CheckRequestPlanner
    participant Runner as CheckRunner
    participant Scope as scopes / gitignore
    participant Plan as planning/requests
    participant Adapter as adapter/argv
    participant Env as environment
    participant Exec as Executor
    participant Norm as normalizer
    participant Fmt as formatters
    participant Store as ReportStore
    participant Disk as .shipgate/reports/

    User->>CLI: shipgate check --target .
    CLI->>App: check(RunCommand)
    App->>Ctx: load_config, resolve_runnables, resolve_environment
    Ctx-->>App: RunContext (planned_checks, suite_id)

    loop each PlannedCheck
        Runner->>Planner: prepare_check(planned, command, context)
        Planner->>Scope: resolve_scope, scope_paths_for_tool
        Scope-->>Planner: scoped paths (gitignore-filtered in check mode)
        alt no matching paths
            Planner-->>Runner: PreparedCheck with skipped CheckReport
        else executable check
            Planner->>Plan: build_execution_request
            Planner->>Plan: resolve_request (options, defaults, output_path)
            Plan-->>Planner: ResolvedRequest
            Planner-->>Runner: PreparedCheck with ResolvedRequest

            alt gate tool (capabilities: Gates)
                Runner->>Runner: prepare_gate_execution (bash + SHIPGATE_* env)
            else catalog tool
                Runner->>Env: resolve_executable (managed venv / PATH)
                Runner->>Adapter: build_argv(resolved)
                Adapter-->>Runner: argv tuple
            end

            Runner->>Exec: subprocess.run(argv, cwd=project_root)
            Exec-->>Runner: ProcessResult (stdout, stderr, exit_code)
            Runner->>Disk: write_raw_output
            Runner->>Norm: normalizer.normalize(resolved, result)
            Norm-->>Runner: CheckReport (findings, status)
        end
    end

    Runner-->>App: list[CheckReport]
    App->>App: build_run_report

    alt run failed
        App->>Fmt: get_formatter(error_format).render(report)
        Fmt-->>User: stderr (compact / json / text / github)
        App->>Store: save_final (failures/ + runs/ + index)
    else run passed
        App->>Store: save_final (runs/ + index, if write_reports)
        opt verbose
            App->>Fmt: json formatter → stdout
        end
    end
```

`prepare_check` applies project `scopes`, per-check overrides, `.gitignore` filtering (check mode), and optional incremental (`--changed-only`, `--since`) trimming, then either returns a skip report or a `ResolvedRequest`. `CheckRunner` owns argv execution, raw output, and normalization. `ReportStore.save_final` owns final report persistence: failed runs write `.shipgate/reports/failures/<run_id>/report.json` and set `report_path`, and every completed run is indexed under `.shipgate/reports/runs/`.

### Data objects at layer boundaries

```mermaid
flowchart TB
    YAML2["shipgate.yaml"] --> PC["ProjectConfig — domain/project.py"]
    CatYAML["catalog tools/suites/workflows YAML"] --> TD["ToolDefinition, SuiteDefinition — domain/catalog.py"]
    PC --> ER["ExecutionRequest — domain/execution.py"]
    TD --> ER
    ER --> RR["ResolvedRequest"]
    RR --> Argv2["argv: tuple[str, ...]"]
    Argv2 --> PR["ProcessResult"]
    PR --> CR["CheckReport — domain/reports.py"]
    CR --> RunR["RunReport"]
    RunR --> Out["formatter output / ReportStore JSON"]
```

`ExecutionRequest` is the internal API (ADR-002): CLI, Python API, batch files, and the frontend orchestrator all converge on the same types before planning and execution diverge per tool.

## Related docs

- Design narrative: `docs/sdd.md` (especially §9 Execution pipeline)
- File-level guide: `docs/implementation.md`
- Layer rules: `.cursor/rules/architecture.mdc`
- ADR index: `docs/adr-support.md`
