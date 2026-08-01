"""Scheduler and interrupt activity collector (FR-004)."""

from __future__ import annotations

from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import read_lines, require_linux


def _loadavg() -> dict[str, Any]:
    text = read_lines("/proc/loadavg")
    if not text:
        return {}
    parts = text[0].split()
    if len(parts) < 5:
        return {}
    running, total = parts[3].split("/")
    return {
        "load_1m": float(parts[0]),
        "load_5m": float(parts[1]),
        "load_15m": float(parts[2]),
        "runnable": int(running),
        "total_processes": int(total),
    }


def _stat_summary() -> dict[str, Any]:
    """Pull aggregate ctxt/processes/procs_running from /proc/stat's non-'cpu' lines."""
    summary: dict[str, Any] = {}
    for line in read_lines("/proc/stat"):
        parts = line.split()
        if not parts:
            continue
        key = parts[0]
        if key in ("ctxt", "processes", "procs_running", "procs_blocked", "softirq"):
            summary[key] = int(parts[1]) if len(parts) > 1 else None
    return summary


def _softirq_hardirq_totals() -> dict[str, int]:
    """Sum the per-CPU columns of /proc/interrupts and /proc/softirqs into one total per line."""

    def _sum_line(parts: list[str]) -> int:
        total = 0
        for token in parts:
            if token.isdigit():
                total += int(token)
        return total

    totals: dict[str, int] = {}
    for path, prefix in (("/proc/softirqs", "softirq_"), ("/proc/interrupts", "irq_")):
        for line in read_lines(path)[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0].rstrip(":")
            totals[f"{prefix}{name}"] = _sum_line(parts[1:])
    return totals


@register_collector
class SchedulerCollector(Collector):
    name = "scheduler"

    def collect(self) -> dict[str, Any]:
        require_linux()
        return {
            "loadavg": _loadavg(),
            "stat": _stat_summary(),
            "irq_totals": _softirq_hardirq_totals(),
        }
