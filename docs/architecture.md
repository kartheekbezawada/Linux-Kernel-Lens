# Architecture

## Pipeline

```
Collector.collect() -> CollectionResult
                              |
                              v
Analyzer.analyze(results) -> [Recommendation, ...]
                              |
                              v
                    reporting.render(format)
```

A **Collector** reads one area of system state (CPU, NUMA, memory, disk,
network, scheduler, kernel sysctls) and returns a `CollectionResult`. It
never writes anything and never raises out of `run()` -- a failing collector
produces a `FAILED` result instead of crashing the whole scan (see
`core/base.py`).

An **Analyzer** takes the full dict of `CollectionResult`s (keyed by
collector name) and returns zero or more `Recommendation`s: severity,
problem, evidence, a concrete fix, and an optional expected improvement.

The **recommendation engine** (`recommendations/engine.py`) ties these
together: `run_collectors()` executes every registered collector,
`run_analyzers()` feeds the results to every registered analyzer, and
`generate_recommendations()` does both and sorts the output by severity.

## Registration

Collectors and analyzers register themselves via decorators:

```python
@register_collector
class CpuCollector(Collector):
    name = "cpu"
    def collect(self) -> dict: ...
```

```python
@register_analyzer
class KernelSysctlAnalyzer(Analyzer):
    name = "kernel_sysctl"
    def analyze(self, results) -> list[Recommendation]: ...
```

The CLI's `_load_collectors()` just needs one import line added per new
collector package -- the registry and recommendation engine pick it up
automatically, no other code changes needed.

## Safety

- Every proc/sysfs read goes through `utils/procfs.py`, which returns `None`
  or `[]` for missing files instead of raising, and raises
  `PermissionDeniedError` specifically for `EACCES` (so "not present" and
  "blocked" are distinguishable).
- `optimizers/sysctl_optimizer.py` is the only module in the codebase that
  writes to the system. `plan_changes()` is read-only; `apply_change()` is
  only reachable from the CLI after `--apply` and an interactive
  confirmation prompt.

## Package layout

| Package | Responsibility |
|---|---|
| `core` | Base classes, result types, registries, exceptions |
| `utils` | Logging, safe proc/sysfs readers |
| `cpu`, `numa`, `memory`, `disk`, `network`, `scheduler`, `kernel` | Collectors (one per hardware/OS area) |
| `recommendations` | Orchestrates collectors + analyzers |
| `reporting` | JSON/YAML/Markdown/CSV renderers |
| `config` | Workload profiles (`profiles/*.yaml`) and user settings |
| `optimizers` | Applies profile sysctl values, with confirmation gating |
| `benchmark` | CPU/memory/disk/network baseline benchmarks |
| `cli` | `linux-opt` entrypoint: `scan`, `analyze`, `benchmark`, `tune` |
