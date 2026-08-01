"""Flags TCP connection-state and interface error issues (FR-007)."""

from __future__ import annotations

from linux_opt.core.base import Analyzer
from linux_opt.core.registry import register_analyzer
from linux_opt.core.result import CollectionResult, Recommendation, Severity

# TCP state codes as they appear in /proc/net/tcp (hex strings, per kernel source)
TIME_WAIT_STATE = "06"
TIME_WAIT_HIGH = 1000
INTERFACE_ERROR_THRESHOLD = 100


@register_analyzer
class NetworkAnalyzer(Analyzer):
    name = "network_analyzer"

    def analyze(self, results: dict[str, CollectionResult]) -> list[Recommendation]:
        network_result = results.get("network")
        if network_result is None or not network_result.ok:
            return []

        data = network_result.data
        recommendations: list[Recommendation] = []

        time_wait_count = data.get("tcp_socket_states", {}).get(TIME_WAIT_STATE, 0)
        if time_wait_count >= TIME_WAIT_HIGH:
            recommendations.append(
                Recommendation(
                    severity=Severity.MEDIUM,
                    problem="Large number of TCP sockets stuck in TIME_WAIT",
                    evidence=f"{time_wait_count} sockets in TIME_WAIT",
                    recommendation="Enable net.ipv4.tcp_tw_reuse if this host makes many short-lived "
                    "outbound connections, or investigate connection churn in the application",
                    source="network_analyzer",
                )
            )

        for name, iface in data.get("interfaces", {}).items():
            rx_errors = iface.get("rx", {}).get("errs", 0) + iface.get("rx", {}).get("drop", 0)
            tx_errors = iface.get("tx", {}).get("errs", 0) + iface.get("tx", {}).get("drop", 0)
            if rx_errors + tx_errors >= INTERFACE_ERROR_THRESHOLD:
                recommendations.append(
                    Recommendation(
                        severity=Severity.HIGH,
                        problem=f"Interface {name} has a significant error/drop count",
                        evidence=f"rx_errors+drops={rx_errors}, tx_errors+drops={tx_errors}",
                        recommendation=f"Check {name}'s physical link (duplex mismatch, bad cable/SFP) "
                        "or driver/ring-buffer configuration",
                        source="network_analyzer",
                    )
                )

        return recommendations
