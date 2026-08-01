# CLI Reference

## `linux-opt scan`

Runs every registered collector and prints what it found.

```
linux-opt scan [--format text|json]
```

## `linux-opt analyze`

Runs collectors, feeds results to every registered analyzer, and prints
recommendations ranked by severity (critical first), in the
Severity/Problem/Evidence/Recommendation format from FR-009.

```
linux-opt analyze [--format text|json|yaml|markdown|csv] [--output PATH]
```

`--output` writes the report to a file instead of stdout.

## `linux-opt benchmark`

Runs the CPU, memory, disk, and network micro-benchmarks and prints a
baseline. No arguments.

```
linux-opt benchmark
```

## `linux-opt tune`

Applies a workload profile's sysctl values.

```
linux-opt tune --profile NAME [--safe] [--apply]
```

- No flags: dry-run, prints the diff between current and desired values.
- `--safe`: same as no flags -- forces dry-run even if `--apply` is also given.
- `--apply`: after printing the diff, asks for interactive `y/N`
  confirmation before writing anything. Declining leaves the system
  untouched.

Available profile names come from `profiles/*.yaml` (currently `postgres`
and `spark`).
