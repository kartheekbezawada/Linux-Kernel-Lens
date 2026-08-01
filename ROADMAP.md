# Roadmap

## Near term (extends what already exists)

- More plugins from requirements.md section 7: MySQL, Spark, Kubernetes,
  Docker, Nginx, MongoDB, Kafka, Elasticsearch, Oracle, Databricks (Postgres
  and Redis are done)
- Integration tests across the target distros (Ubuntu, Debian, RHEL, Rocky,
  AlmaLinux, SUSE, Fedora) -- current test suite is unit-only
- Two-sample disk/network rate analyzers (real throughput/IOPS/latency,
  which need two readings over a known interval, unlike the current
  point-in-time capacity/queue-depth checks)
- Functional and performance test tiers, and the 90% unit coverage target

## Longer term (from requirements.md section 8)

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

None of the longer-term items are scheduled -- they're captured here so
scope decisions on nearer-term work can be made with the eventual direction
in mind (e.g., keeping collector output JSON-serializable now makes a future
REST API or Prometheus exporter simpler later).
