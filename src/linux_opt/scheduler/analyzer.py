"""Flags run-queue and blocked-process pressure (FR-004).

Cross-references CpuCollector's online CPU count with SchedulerCollector's
load average, since "load average of 8" means very different things on a
2-core box vs a 64-core box.
"""

from __future__ import annotations

from linux_opt.core.base import Analyzer
from linux_opt.core.registry import register_analyzer
from linux_opt.core.result import CollectionResult, Recommendation, Severity

LOAD_PER_CPU_HIGH = 1.5
PROCS_BLOCKED_HIGH = 5


@register_analyzer
class SchedulerAnalyzer(Analyzer):
    name = "scheduler_analyzer"

    def analyze(self, results: dict[str, CollectionResult]) -> list[Recommendation]:
        scheduler_result = results.get("scheduler")
        if scheduler_result is None or not scheduler_result.ok:
            return []

        data = scheduler_result.data
        recommendations: list[Recommendation] = []

        load_1m = data.get("loadavg", {}).get("load_1m")
        online_cpus = self._online_cpus(results)
        if load_1m is not None and online_cpus:
            load_per_cpu = load_1m / online_cpus
            if load_per_cpu >= LOAD_PER_CPU_HIGH:
                recommendations.append(
                    Recommendation(
                        severity=Severity.HIGH,
                        problem="System load average is high relative to CPU count",
                        evidence=f"load_1m={load_1m} across {online_cpus} CPUs ({load_per_cpu:.2f} per CPU)",
                        recommendation="Investigate what's driving load -- check for CPU-bound "
                        "processes, excessive context switching, or insufficient CPU capacity "
                        "for the current workload",
                        source="scheduler_analyzer",
                    )
                )

        procs_blocked = data.get("stat", {}).get("procs_blocked")
        if procs_blocked is not None and procs_blocked >= PROCS_BLOCKED_HIGH:
            recommendations.append(
                Recommendation(
                    severity=Severity.MEDIUM,
                    problem="Multiple processes blocked in uninterruptible sleep",
                    evidence=f"procs_blocked={procs_blocked}",
                    recommendation="Processes in uninterruptible sleep are usually waiting on IO -- "
                    "check disk/network latency rather than CPU scheduling",
                    source="scheduler_analyzer",
                )
            )

        return recommendations

    @staticmethod
    def _online_cpus(results: dict[str, CollectionResult]) -> int | None:
        cpu_result = results.get("cpu")
        if cpu_result is None or not cpu_result.ok:
            return None
        return cpu_result.data.get("online_cpus")
