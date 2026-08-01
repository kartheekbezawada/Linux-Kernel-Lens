"""Storage device and filesystem collector (FR-006)."""

from __future__ import annotations

import shutil
from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import list_dir, read_lines, require_linux

# /proc/diskstats field layout: https://www.kernel.org/doc/Documentation/iostats.txt
DISKSTATS_FIELDS = [
    "reads_completed",
    "reads_merged",
    "sectors_read",
    "ms_reading",
    "writes_completed",
    "writes_merged",
    "sectors_written",
    "ms_writing",
    "ios_in_progress",
    "ms_doing_io",
    "weighted_ms_doing_io",
]


def _block_devices() -> list[str]:
    return list_dir("/sys/block")


def _diskstats(whole_disks: list[str]) -> dict[str, dict[str, int]]:
    """Parse /proc/diskstats, keeping only whole-disk devices (skip partitions)."""
    devices: dict[str, dict[str, int]] = {}
    for line in read_lines("/proc/diskstats"):
        parts = line.split()
        if len(parts) < 3 + len(DISKSTATS_FIELDS):
            continue
        name = parts[2]
        if name not in whole_disks:
            continue
        values = parts[3 : 3 + len(DISKSTATS_FIELDS)]
        devices[name] = dict(zip(DISKSTATS_FIELDS, (int(v) for v in values)))
    return devices


def _filesystem_usage() -> list[dict[str, Any]]:
    """Usage for common mount points; avoids pulling in a mtab parser dependency."""
    candidates = ["/", "/home", "/var", "/tmp", "/boot"]
    usage = []
    for path in candidates:
        try:
            total, used, free = shutil.disk_usage(path)
        except (FileNotFoundError, OSError):
            continue
        usage.append(
            {
                "path": path,
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "used_pct": round((used / total) * 100, 1) if total else 0.0,
            }
        )
    return usage


@register_collector
class DiskCollector(Collector):
    name = "disk"

    def collect(self) -> dict[str, Any]:
        require_linux()
        whole_disks = _block_devices()
        return {
            "block_devices": whole_disks,
            "diskstats": _diskstats(whole_disks),
            "filesystems": _filesystem_usage(),
        }
