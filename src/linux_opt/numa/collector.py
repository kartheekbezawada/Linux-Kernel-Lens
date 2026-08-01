"""NUMA topology and per-node memory locality collector (FR-001)."""

from __future__ import annotations

from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import list_dir, read_text, require_linux

NODE_ROOT = "/sys/devices/system/node"


def _node_ids() -> list[int]:
    ids = []
    for entry in list_dir(NODE_ROOT):
        if entry.startswith("node") and entry[4:].isdigit():
            ids.append(int(entry[4:]))
    return sorted(ids)


def _node_meminfo(node_id: int) -> dict[str, str]:
    """Parse .../nodeN/meminfo, which is shaped like 'Node 0 MemTotal:  N kB'."""
    raw = read_text(f"{NODE_ROOT}/node{node_id}/meminfo") or ""
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().split()[-1]
        parsed[key] = value.strip()
    return parsed


def _node_cpus(node_id: int) -> str:
    return (read_text(f"{NODE_ROOT}/node{node_id}/cpulist") or "").strip()


def _node_distances(node_id: int) -> list[int]:
    raw = (read_text(f"{NODE_ROOT}/node{node_id}/distance") or "").split()
    return [int(v) for v in raw if v.isdigit()]


@register_collector
class NumaCollector(Collector):
    name = "numa"

    def collect(self) -> dict[str, Any]:
        require_linux()
        node_ids = _node_ids()
        nodes: dict[str, Any] = {}
        for node_id in node_ids:
            nodes[f"node{node_id}"] = {
                "cpus": _node_cpus(node_id),
                "meminfo": _node_meminfo(node_id),
                "distance": _node_distances(node_id),
            }
        return {
            "node_count": len(node_ids),
            "numa_enabled": len(node_ids) > 1,
            "nodes": nodes,
        }
