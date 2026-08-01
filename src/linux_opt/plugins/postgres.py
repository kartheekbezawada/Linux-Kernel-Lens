"""Postgres workload plugin.

Deliberately doesn't connect to the database (no credentials assumed
available, and this project's collectors are OS-level/read-only by design).
Everything here comes from process-table inspection, which is enough to
flag connection-count risk without needing DB access.
"""

from __future__ import annotations

from typing import Any

from linux_opt.core.result import Recommendation, Severity
from linux_opt.plugins.base import Plugin, register_plugin
from linux_opt.utils.procfs import list_dir, read_text

# A default max_connections of 100 is Postgres's out-of-the-box setting;
# this is a heuristic trigger point, not a hard limit -- real deployments
# often raise max_connections deliberately and that's fine.
BACKEND_COUNT_WARNING = 80


def _postgres_pids() -> list[int]:
    pids = []
    for entry in list_dir("/proc"):
        if not entry.isdigit():
            continue
        comm = (read_text(f"/proc/{entry}/comm") or "").strip()
        if comm in ("postgres", "postmaster"):
            pids.append(int(entry))
    return pids


@register_plugin
class PostgresPlugin(Plugin):
    name = "postgres"

    def detect(self) -> bool:
        return len(_postgres_pids()) > 0

    def collect(self) -> dict[str, Any]:
        pids = _postgres_pids()
        return {"backend_process_count": len(pids)}

    def analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        count = data.get("backend_process_count", 0)
        if count >= BACKEND_COUNT_WARNING:
            recommendations.append(
                Recommendation(
                    severity=Severity.MEDIUM,
                    problem="High number of Postgres backend processes",
                    evidence=f"{count} postgres/postmaster processes running",
                    recommendation="Approaching or at Postgres's default max_connections=100 -- "
                    "consider a connection pooler (pgbouncer) instead of raising "
                    "max_connections further, since each backend consumes real memory",
                    source="postgres",
                )
            )
        return recommendations
