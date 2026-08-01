"""Flags NUMA memory imbalance across nodes (FR-009's headline example)."""

from __future__ import annotations

from linux_opt.core.base import Analyzer
from linux_opt.core.registry import register_analyzer
from linux_opt.core.result import CollectionResult, Recommendation, Severity

# A node using >80% of its memory while another uses <20% is the kind of skew
# that suggests workloads aren't being scheduled/allocated with NUMA locality
# in mind -- these thresholds are a starting heuristic, not a hard science.
HIGH_USAGE_PCT = 80.0
LOW_USAGE_PCT = 20.0


def _used_pct(meminfo: dict[str, str]) -> float | None:
    total = meminfo.get("MemTotal", "").split()
    free = meminfo.get("MemFree", "").split()
    if not total or not free or not total[0].isdigit() or not free[0].isdigit():
        return None
    total_kb, free_kb = int(total[0]), int(free[0])
    if total_kb == 0:
        return None
    return round((total_kb - free_kb) / total_kb * 100, 1)


@register_analyzer
class NumaImbalanceAnalyzer(Analyzer):
    name = "numa_imbalance"

    def analyze(self, results: dict[str, CollectionResult]) -> list[Recommendation]:
        numa_result = results.get("numa")
        if numa_result is None or not numa_result.ok:
            return []

        data = numa_result.data
        if not data.get("numa_enabled"):
            return []  # single-node systems can't have cross-node imbalance

        usage_by_node: dict[str, float] = {}
        for node_name, node_data in data.get("nodes", {}).items():
            pct = _used_pct(node_data.get("meminfo", {}))
            if pct is not None:
                usage_by_node[node_name] = pct

        if len(usage_by_node) < 2:
            return []

        busiest = max(usage_by_node, key=usage_by_node.get)
        idlest = min(usage_by_node, key=usage_by_node.get)
        if usage_by_node[busiest] < HIGH_USAGE_PCT or usage_by_node[idlest] > LOW_USAGE_PCT:
            return []

        return [
            Recommendation(
                severity=Severity.HIGH,
                problem="NUMA memory usage is imbalanced across nodes",
                evidence=(
                    f"{busiest} at {usage_by_node[busiest]}% memory used, "
                    f"{idlest} at {usage_by_node[idlest]}% used"
                ),
                recommendation=(
                    f"Investigate workloads on {busiest} for NUMA affinity; consider binding "
                    f"memory-heavy processes to under-used nodes like {idlest} with numactl"
                ),
                expected_improvement="12-18%",
                source="numa_imbalance",
            )
        ]
