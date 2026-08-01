"""CPU topology and cache hierarchy collector (FR-001)."""

from __future__ import annotations

from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import list_dir, read_lines, read_text, require_linux

CPU_SYS_PATH = "/sys/devices/system/cpu"


def _parse_cpuinfo() -> list[dict[str, str]]:
    """Split /proc/cpuinfo into one dict per logical CPU block."""
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in read_lines("/proc/cpuinfo"):
        if not line.strip():
            if current:
                blocks.append(current)
                current = {}
            continue
        key, _, value = line.partition(":")
        current[key.strip()] = value.strip()
    if current:
        blocks.append(current)
    return blocks


def _topology(logical_cpus: list[dict[str, str]]) -> dict[str, Any]:
    sockets: set[str] = set()
    cores: set[tuple[str, str]] = set()
    for cpu in logical_cpus:
        phys_id = cpu.get("physical id", "0")
        core_id = cpu.get("core id", "0")
        sockets.add(phys_id)
        cores.add((phys_id, core_id))
    return {
        "logical_cpus": len(logical_cpus),
        "sockets": len(sockets) or 1,
        "cores_per_socket": len(cores) // max(len(sockets), 1) if cores else None,
        "threads_per_core": (
            len(logical_cpus) // len(cores) if cores else None
        ),
        "model_name": logical_cpus[0].get("model name") if logical_cpus else None,
    }


def _cache_hierarchy() -> dict[str, Any]:
    """Read per-cache-index size/level/type from sysfs for logical CPU 0."""
    caches: dict[str, Any] = {}
    cache_root = f"{CPU_SYS_PATH}/cpu0/cache"
    for entry in list_dir(cache_root):
        if not entry.startswith("index"):
            continue
        base = f"{cache_root}/{entry}"
        level = read_text(f"{base}/level")
        cache_type = read_text(f"{base}/type")
        size = read_text(f"{base}/size")
        if level is None:
            continue
        key = f"L{level.strip()}-{(cache_type or '').strip()}".rstrip("-")
        caches[key] = (size or "").strip()
    return caches


@register_collector
class CpuCollector(Collector):
    name = "cpu"

    def collect(self) -> dict[str, Any]:
        require_linux()
        logical_cpus = _parse_cpuinfo()
        return {
            "topology": _topology(logical_cpus),
            "cache": _cache_hierarchy(),
            "online_cpus": len(
                [e for e in list_dir(CPU_SYS_PATH) if e.startswith("cpu") and e[3:].isdigit()]
            ),
        }
