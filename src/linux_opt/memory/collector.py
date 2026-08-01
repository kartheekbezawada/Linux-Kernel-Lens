"""Memory subsystem collector: meminfo, huge pages, THP, slab, swap (FR-005)."""

from __future__ import annotations

from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import read_kv_file, read_text, require_linux

MEMINFO_FIELDS = [
    "MemTotal",
    "MemFree",
    "MemAvailable",
    "Buffers",
    "Cached",
    "SwapTotal",
    "SwapFree",
    "Dirty",
    "Writeback",
    "AnonHugePages",
    "HugePages_Total",
    "HugePages_Free",
    "Hugepagesize",
    "Slab",
    "SReclaimable",
    "SUnreclaim",
]


def _meminfo() -> dict[str, str]:
    raw = read_kv_file("/proc/meminfo")
    return {field: raw[field] for field in MEMINFO_FIELDS if field in raw}


def _transparent_hugepage() -> dict[str, str]:
    enabled = read_text("/sys/kernel/mm/transparent_hugepage/enabled")
    defrag = read_text("/sys/kernel/mm/transparent_hugepage/defrag")
    return {
        "enabled": (enabled or "").strip(),
        "defrag": (defrag or "").strip(),
    }


def _swap_usage(meminfo: dict[str, str]) -> dict[str, Any]:
    def _kb(value: str) -> int:
        return int(value.split()[0]) if value else 0

    total = _kb(meminfo.get("SwapTotal", "0"))
    free = _kb(meminfo.get("SwapFree", "0"))
    used = total - free
    return {
        "total_kb": total,
        "used_kb": used,
        "used_pct": round((used / total) * 100, 1) if total else 0.0,
    }


@register_collector
class MemoryCollector(Collector):
    name = "memory"

    def collect(self) -> dict[str, Any]:
        require_linux()
        meminfo = _meminfo()
        return {
            "meminfo": meminfo,
            "transparent_hugepage": _transparent_hugepage(),
            "swap": _swap_usage(meminfo),
        }
