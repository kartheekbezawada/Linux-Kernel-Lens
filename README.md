# Linux Kernel Lens

A Linux system discovery, performance analysis, and tuning toolkit. It reads
hardware and OS state through `/proc` and `/sys`, flags common
misconfigurations, and can optionally apply workload-specific tuning
profiles.

See [requirements.md](requirements.md) for the full functional/non-functional
spec this project is built against.

## Status

Core pipeline (collect -> analyze -> report) is implemented for CPU, NUMA,
memory, disk, network, scheduler, process, OS/distro, and kernel sysctl
data, with analyzers turning most of that into recommendations. Postgres
and Redis plugins exist; the rest of requirements.md section 7's plugin
list (MySQL, Spark, Kubernetes, Kafka, etc.) doesn't yet.

The repository only contains folders/files that are actually used --
requirements.md documents a larger aspirational structure (docker/,
examples/, additional test tiers, a full plugin directory per workload,
etc.) that hasn't been built yet. See [ROADMAP.md](ROADMAP.md) for what's
planned next.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Discover hardware/OS state
linux-opt scan
linux-opt scan --format json

# Run collectors + analyzers, print ranked recommendations
linux-opt analyze
linux-opt analyze --format markdown --output report.md

# CPU/memory/disk/network baseline
linux-opt benchmark

# Apply a workload tuning profile (dry-run by default)
linux-opt tune --profile postgres
linux-opt tune --profile spark --apply
```

`tune` never writes anything without `--apply`, and even with `--apply` it
asks for interactive confirmation before touching any sysctl value.

## Architecture

See [docs/architecture.md](docs/architecture.md) for how collectors,
analyzers, and the recommendation engine fit together, and
[docs/cli_reference.md](docs/cli_reference.md) for full command details.

## Development

```bash
pip install -e ".[dev]"
```

Collectors and analyzers self-register via `@register_collector` /
`@register_analyzer` decorators -- adding a new one doesn't require touching
the CLI or the recommendation engine.
