"""Redis workload plugin.

Checks the two OS-level settings Redis's own documentation explicitly
calls out as needing attention (vm.overcommit_memory and THP) -- both are
things this project already knows how to read, so this plugin adds no new
collection mechanism, just Redis-specific interpretation of existing
system state.
"""

from __future__ import annotations

from typing import Any

from linux_opt.core.result import Recommendation, Severity
from linux_opt.plugins.base import Plugin, register_plugin
from linux_opt.utils.procfs import list_dir, read_text


def _redis_running() -> bool:
    for entry in list_dir("/proc"):
        if not entry.isdigit():
            continue
        comm = (read_text(f"/proc/{entry}/comm") or "").strip()
        if comm == "redis-server":
            return True
    return False


@register_plugin
class RedisPlugin(Plugin):
    name = "redis"

    def detect(self) -> bool:
        return _redis_running()

    def collect(self) -> dict[str, Any]:
        return {
            "overcommit_memory": (read_text("/proc/sys/vm/overcommit_memory") or "").strip(),
            "thp_enabled": (read_text("/sys/kernel/mm/transparent_hugepage/enabled") or "").strip(),
        }

    def analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        recommendations: list[Recommendation] = []

        if data.get("overcommit_memory") not in ("1", ""):
            recommendations.append(
                Recommendation(
                    severity=Severity.MEDIUM,
                    problem="vm.overcommit_memory is not set to 1 on a Redis host",
                    evidence=f"vm.overcommit_memory={data.get('overcommit_memory')}",
                    recommendation="Set vm.overcommit_memory=1 -- Redis's background save forks the "
                    "process, and without overcommit enabled that fork can fail under memory "
                    "pressure even though it won't actually need the full extra memory",
                    source="redis",
                )
            )

        if "[always]" in data.get("thp_enabled", ""):
            recommendations.append(
                Recommendation(
                    severity=Severity.HIGH,
                    problem="Transparent Huge Pages enabled on a Redis host",
                    evidence=f"transparent_hugepage/enabled={data.get('thp_enabled')}",
                    recommendation="Disable THP (set to 'never' or 'madvise') -- Redis's own docs "
                    "warn THP causes significant latency spikes during background saves",
                    source="redis",
                )
            )

        return recommendations
