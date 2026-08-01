"""Flags poor sysctl configurations detected by KernelCollector (FR-008)."""

from __future__ import annotations

from linux_opt.core.base import Analyzer
from linux_opt.core.result import CollectionResult, Recommendation, Severity


def _as_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


class KernelSysctlAnalyzer(Analyzer):
    name = "kernel_sysctl"

    def analyze(self, results: dict[str, CollectionResult]) -> list[Recommendation]:
        kernel_result = results.get("kernel")
        if kernel_result is None or not kernel_result.ok:
            return []

        sysctl = kernel_result.data.get("sysctl", {})
        recommendations: list[Recommendation] = []

        swappiness = _as_int(sysctl.get("vm.swappiness"))
        if swappiness is not None and swappiness > 60:
            recommendations.append(
                Recommendation(
                    severity=Severity.MEDIUM,
                    problem="vm.swappiness is high for a server workload",
                    evidence=f"vm.swappiness={swappiness}",
                    recommendation="Lower vm.swappiness to 10-30 unless this host is memory-constrained by design",
                    source="kernel_sysctl",
                )
            )

        overcommit = _as_int(sysctl.get("vm.overcommit_memory"))
        if overcommit == 0:
            recommendations.append(
                Recommendation(
                    severity=Severity.LOW,
                    problem="vm.overcommit_memory uses heuristic overcommit",
                    evidence="vm.overcommit_memory=0",
                    recommendation="Consider overcommit_memory=2 with overcommit_ratio tuned for predictable OOM behavior on memory-sensitive workloads",
                    source="kernel_sysctl",
                )
            )

        somaxconn = _as_int(sysctl.get("net.core.somaxconn"))
        if somaxconn is not None and somaxconn < 1024:
            recommendations.append(
                Recommendation(
                    severity=Severity.MEDIUM,
                    problem="net.core.somaxconn is low for a high-connection-rate service",
                    evidence=f"net.core.somaxconn={somaxconn}",
                    recommendation="Raise net.core.somaxconn to 1024+ to avoid dropped connections under burst load",
                    source="kernel_sysctl",
                )
            )

        tw_reuse = _as_int(sysctl.get("net.ipv4.tcp_tw_reuse"))
        if tw_reuse == 0:
            recommendations.append(
                Recommendation(
                    severity=Severity.LOW,
                    problem="net.ipv4.tcp_tw_reuse is disabled",
                    evidence="net.ipv4.tcp_tw_reuse=0",
                    recommendation="Enable tcp_tw_reuse (=1) on servers making many outbound connections to reclaim TIME_WAIT sockets faster",
                    source="kernel_sysctl",
                )
            )

        return recommendations
