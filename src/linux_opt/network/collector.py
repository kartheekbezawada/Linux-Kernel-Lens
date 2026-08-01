"""Network interface, socket, and TCP stats collector (FR-007)."""

from __future__ import annotations

from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import read_lines, read_text, require_linux

# /proc/net/dev columns after the interface name, receive then transmit
RX_FIELDS = ["bytes", "packets", "errs", "drop", "fifo", "frame", "compressed", "multicast"]
TX_FIELDS = ["bytes", "packets", "errs", "drop", "fifo", "collisions", "carrier", "compressed"]


def _interfaces() -> dict[str, dict[str, Any]]:
    interfaces: dict[str, dict[str, Any]] = {}
    lines = read_lines("/proc/net/dev")[2:]  # first two lines are headers
    for line in lines:
        if ":" not in line:
            continue
        name, _, rest = line.partition(":")
        name = name.strip()
        values = rest.split()
        if len(values) < len(RX_FIELDS) + len(TX_FIELDS):
            continue
        rx = dict(zip(RX_FIELDS, (int(v) for v in values[: len(RX_FIELDS)])))
        tx = dict(
            zip(TX_FIELDS, (int(v) for v in values[len(RX_FIELDS) : len(RX_FIELDS) + len(TX_FIELDS)]))
        )
        interfaces[name] = {"rx": rx, "tx": tx}
    return interfaces


def _interface_state(name: str) -> str:
    return (read_text(f"/sys/class/net/{name}/operstate") or "unknown").strip()


def _tcp_retransmits() -> int | None:
    """Sum retransmit segments from /proc/net/snmp's Tcp line."""
    lines = read_lines("/proc/net/snmp")
    header, values = None, None
    for i, line in enumerate(lines):
        if line.startswith("Tcp:") and header is None:
            header = line.split()[1:]
        elif line.startswith("Tcp:") and values is None:
            values = line.split()[1:]
            break
    if not header or not values:
        return None
    stats = dict(zip(header, values))
    return int(stats["RetransSegs"]) if "RetransSegs" in stats else None


def _socket_summary() -> dict[str, int]:
    """Count TCP sockets per state code from /proc/net/tcp (+tcp6 if present)."""
    counts: dict[str, int] = {}
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        for line in read_lines(path)[1:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            state = parts[3]
            counts[state] = counts.get(state, 0) + 1
    return counts


@register_collector
class NetworkCollector(Collector):
    name = "network"

    def collect(self) -> dict[str, Any]:
        require_linux()
        interfaces = _interfaces()
        for name in interfaces:
            interfaces[name]["state"] = _interface_state(name)
        return {
            "interfaces": interfaces,
            "tcp_retransmits": _tcp_retransmits(),
            "tcp_socket_states": _socket_summary(),
        }
