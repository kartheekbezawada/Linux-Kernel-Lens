"""Flags filesystem capacity and IO queue-depth issues (FR-006).

diskstats is a point-in-time cumulative counter snapshot, so this analyzer
can't derive throughput/IOPS/latency (that needs two samples over a known
interval) -- it checks the two things a single scan CAN say something useful
about: filesystem fill level and IO requests queued right now.
"""

from __future__ import annotations

from linux_opt.core.base import Analyzer
from linux_opt.core.registry import register_analyzer
from linux_opt.core.result import CollectionResult, Recommendation, Severity

FS_USAGE_HIGH_PCT = 90.0
IOS_IN_PROGRESS_HIGH = 10


@register_analyzer
class DiskAnalyzer(Analyzer):
    name = "disk_analyzer"

    def analyze(self, results: dict[str, CollectionResult]) -> list[Recommendation]:
        disk_result = results.get("disk")
        if disk_result is None or not disk_result.ok:
            return []

        data = disk_result.data
        recommendations: list[Recommendation] = []

        for fs in data.get("filesystems", []):
            if fs.get("used_pct", 0) >= FS_USAGE_HIGH_PCT:
                recommendations.append(
                    Recommendation(
                        severity=Severity.HIGH,
                        problem=f"Filesystem {fs['path']} is nearly full",
                        evidence=f"{fs['used_pct']}% used ({fs['used_bytes'] // (1024**3)} GB of "
                        f"{fs['total_bytes'] // (1024**3)} GB)",
                        recommendation=f"Free up space on {fs['path']} or extend the volume before "
                        "it fills completely and writes start failing",
                        source="disk_analyzer",
                    )
                )

        for device, stats in data.get("diskstats", {}).items():
            in_progress = stats.get("ios_in_progress", 0)
            if in_progress >= IOS_IN_PROGRESS_HIGH:
                recommendations.append(
                    Recommendation(
                        severity=Severity.MEDIUM,
                        problem=f"Device {device} has a deep IO queue at scan time",
                        evidence=f"ios_in_progress={in_progress}",
                        recommendation=f"Check what's driving IO load on {device} -- a sustained "
                        "deep queue suggests the device can't keep up with request volume",
                        source="disk_analyzer",
                    )
                )

        return recommendations
