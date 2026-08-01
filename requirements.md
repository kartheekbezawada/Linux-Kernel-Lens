# Linux Kernel Lens — Requirements

## 1. Functional Requirements

### FR-001 Hardware Discovery
Automatically discover:
- CPU topology (sockets, cores, threads)
- NUMA topology
- L1/L2/L3 cache hierarchy
- Memory channels
- Huge Pages configuration
- PCI devices
- Storage devices
- Network interfaces

### FR-002 Operating System Discovery
Collect:
- Distribution and kernel version
- Kernel configuration
- Boot parameters
- Installed packages
- Systemd services and running daemons

### FR-003 Process Analyzer
Analyze:
- CPU and memory usage
- Context switches
- Thread count
- Scheduling policy and CPU affinity
- NUMA locality
- Open file handles
- Page faults
- Stack usage

### FR-004 Scheduler Analysis
Collect:
- Run queue depth
- Scheduler and wakeup latency
- CPU migrations
- SoftIRQ / HardIRQ activity
- Scheduler statistics

### FR-005 Memory Analysis
Analyze:
- Huge Pages and THP usage
- Slab allocator
- Memory fragmentation
- Swap usage
- Page cache and dirty pages
- NUMA memory locality

### FR-006 Storage Analysis
Measure:
- Read/write throughput
- Queue depth
- Latency and IOPS
- Filesystem utilization and type

### FR-007 Network Analysis
Collect:
- Throughput and packet loss
- TCP retransmissions
- Socket usage and connection states
- Interface utilization
- IRQ mapping

### FR-008 Kernel Parameter Analysis
Analyze `sysctl` settings across `vm.*`, `net.*`, `fs.*`, and `kernel.*` namespaces, and detect poor configurations.

### FR-009 Recommendation Engine
Produce actionable recommendations, e.g.:

> **Severity:** High
> **Problem:** NUMA imbalance detected
> **Evidence:** 72% remote memory access
> **Recommendation:** Bind process to NUMA node 0
> **Expected Improvement:** 12–18%

### FR-010 Optimization Engine
Provide optional remediation via CLI:
```
linux-opt tune
linux-opt tune --safe
linux-opt tune --profile spark
linux-opt tune --profile postgres
```

### FR-011 Benchmark Engine
Run CPU, memory, disk, and network benchmarks, and generate a performance baseline.

### FR-012 Report Generator
Generate reports in: HTML, JSON, YAML, Markdown, CSV, PDF.

## 2. Non-Functional Requirements

### Performance
- Complete a full system scan in under 30 seconds
- Memory usage under 150 MB
- Startup under 2 seconds
- CPU overhead under 3%

### Scalability
Support:
- Single workstations
- Enterprise and NUMA/multi-socket servers
- Cloud VMs
- Kubernetes nodes

### Reliability
- Gracefully handle missing permissions
- Continue after partial failures
- Retry transient failures
- Structured logging

### Security
- Read-only mode by default
- Explicit confirmation required before modifications
- Least privilege
- Audit log

### Portability
Support: Ubuntu, Debian, RHEL, Rocky, AlmaLinux, SUSE, Fedora.

## 3. Repository Structure
```
linux-opt/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
├── ROADMAP.md
├── RELEASE_NOTES.md
├── requirements.txt
├── pyproject.toml
├── setup.py
├── Makefile
├── tox.ini
├── pytest.ini
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml
├── docker/
├── scripts/
├── docs/
├── examples/
├── benchmarks/
├── configs/
├── policies/
├── profiles/
├── sample_reports/
├── src/
│   └── linux_opt/
├── tests/
├── integration_tests/
├── performance_tests/
├── test_data/
└── ci/
```

## 4. Source Structure
```
src/linux_opt/
├── cli/
├── core/
├── collectors/
├── analyzers/
├── optimizers/
├── benchmark/
├── recommendations/
├── kernel/
├── numa/
├── cpu/
├── memory/
├── disk/
├── network/
├── scheduler/
├── reporting/
├── plugins/
├── config/
└── utils/
```

## 5. Test Structure
```
tests/
├── unit/
├── integration/
├── functional/
├── performance/
├── regression/
└── fixtures/
    ├── mock_proc/
    ├── mock_sys/
    └── golden_reports/
```

**Targets:**
- 90% unit test coverage
- Integration tests across multiple Linux distributions
- Regression tests for recommendation accuracy
- Performance tests for collector overhead

## 6. Documentation
```
docs/
├── architecture.md
├── design.md
├── developer_guide.md
├── plugin_development.md
├── cli_reference.md
├── kernel_metrics.md
├── performance_tuning.md
├── benchmarking.md
├── security.md
├── faq.md
├── troubleshooting.md
├── roadmap.md
├── api_reference.md
└── release_process.md
```

## 7. Plugin System
Support plugins such as:
```
plugins/
├── postgres/
├── mysql/
├── spark/
├── kubernetes/
├── docker/
├── nginx/
├── redis/
├── mongodb/
├── kafka/
├── elasticsearch/
├── oracle/
└── databricks/
```

Each plugin can:
- Collect workload-specific metrics
- Analyze performance
- Generate tailored recommendations
- Apply safe optimizations where appropriate

## 8. Future Roadmap
- eBPF-based collectors for low-overhead tracing
- Rust implementations for performance-critical collectors
- Web dashboard (FastAPI + React)
- Prometheus exporter
- OpenTelemetry integration
- Grafana dashboards
- AI-powered recommendation engine
- Time-series trend analysis
- Kubernetes operator
- Multi-host fleet management
- REST API and gRPC service
- VS Code extension

---

This scope gives the project the feel of a serious engineering platform rather than a utility script. It demonstrates software architecture, operating systems knowledge, performance engineering, testing, documentation, CI/CD, and extensibility — all of which are attractive in senior platform, infrastructure, and systems engineering roles.
