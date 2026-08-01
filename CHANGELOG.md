# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/). This
project doesn't have tagged releases yet, so entries are grouped by the PR
batch that introduced them rather than a version number.

## Unreleased

### Added

- Core `Collector`/`Analyzer` base classes, result model, and registries
- Collectors: CPU, NUMA, memory, disk, network, scheduler, kernel/sysctl,
  process, OS/distro discovery
- Analyzers: kernel sysctl misconfiguration, NUMA imbalance, memory
  (swap/THP/huge pages), disk (capacity/queue depth), network (TIME_WAIT/
  interface errors), scheduler (load/blocked processes)
- Recommendation engine orchestrating all collectors + analyzers, ranked by
  severity
- Report renderers: JSON, YAML, Markdown, CSV, HTML, and a dependency-free
  PDF writer -- all six formats from the original spec
- Workload tuning profiles (postgres, spark) with a confirmation-gated
  sysctl optimizer (`linux-opt tune`)
- Plugin framework (`detect`/`collect`/`analyze`) plus Postgres and Redis
  plugins
- CPU/memory/disk/network micro-benchmarks (`linux-opt benchmark`)
- CLI: `scan`, `analyze`, `benchmark`, `tune`, `plugins`
- First unit test suite (procfs readers, collector/analyzer contracts)
- GitHub Actions CI running the suite across Python 3.10-3.12

### Known gaps

- No integration/functional/performance test tiers yet, only unit
- Only two plugins exist (postgres, redis) out of the full target list in
  requirements.md section 7
- No web dashboard, Prometheus/OpenTelemetry export, or eBPF collectors
  (all explicitly future roadmap items, see ROADMAP.md)
