"""Flags common memory misconfigurations from MemoryCollector's output (FR-005)."""

from __future__ import annotations

from linux_opt.core.base import Analyzer
from linux_opt.core.registry import register_analyzer
from linux_opt.core.result import CollectionResult, Recommendation, Severity

SWAP_USED_HIGH_PCT = 20.0


def _kb(value: str) -> int:
    """Parse a meminfo value like '1234 kB' into an int, or 0 if unparseable."""
    parts = value.split()
    return int(parts[0]) if parts and parts[0].isdigit() else 0


@register_analyzer
class MemoryAnalyzer(Analyzer):
    name = "memory_analyzer"

    def analyze(self, results: dict[str, CollectionResult]) -> list[Recommendation]:
        memory_result = results.get("memory")
        if memory_result is None or not memory_result.ok:
            return []

        data = memory_result.data
        recommendations: list[Recommendation] = []

        swap = data.get("swap", {})
        if swap.get("used_pct", 0) > SWAP_USED_HIGH_PCT and swap.get("total_kb", 0) > 0:
            recommendations.append(
                Recommendation(
                    severity=Severity.HIGH,
                    problem="System is actively swapping",
                    evidence=f"swap used: {swap['used_pct']}% of {swap['total_kb'] // 1024} MB",
                    recommendation="Investigate memory pressure -- check for oversized JVM heaps, "
                    "leaking processes, or insufficient physical RAM for the current workload",
                    source="memory_analyzer",
                )
            )

        thp = data.get("transparent_hugepage", {})
        # sysfs shows the active choice in brackets, e.g. "always [madvise] never"
        if "[always]" in thp.get("enabled", ""):
            recommendations.append(
                Recommendation(
                    severity=Severity.MEDIUM,
                    problem="Transparent Huge Pages set to 'always'",
                    evidence=f"transparent_hugepage/enabled={thp.get('enabled')}",
                    recommendation="Set THP to 'madvise' for latency-sensitive workloads (databases, "
                    "JVMs) -- 'always' can cause unpredictable allocation-stall latency spikes",
                    source="memory_analyzer",
                )
            )

        # HugePages_Total/Free are page counts, not kB, despite going through
        # the same "number [unit]" parser as the kB fields above.
        meminfo = data.get("meminfo", {})
        anon_hp_kb = _kb(meminfo.get("AnonHugePages", "0 kB"))
        huge_pages_free = _kb(meminfo.get("HugePages_Free", "0"))
        huge_pages_total = _kb(meminfo.get("HugePages_Total", "0"))
        if huge_pages_total > 0 and huge_pages_free == huge_pages_total and anon_hp_kb == 0:
            recommendations.append(
                Recommendation(
                    severity=Severity.LOW,
                    problem="Static huge pages are reserved but completely unused",
                    evidence=f"HugePages_Total={huge_pages_total}, HugePages_Free={huge_pages_free}",
                    recommendation="Either configure an application to use the reserved huge pages "
                    "or reduce vm.nr_hugepages to free that memory for general use",
                    source="memory_analyzer",
                )
            )

        return recommendations
