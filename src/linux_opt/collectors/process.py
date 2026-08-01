"""Per-process resource usage collector (FR-003).

Reads directly from /proc/[pid]/* instead of going through psutil so the
output stays consistent with every other collector in this codebase (raw
procfs fields, same defensive read helpers). psutil is still a declared
dependency for later cross-platform needs, just not used here.
"""

from __future__ import annotations

from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import list_dir, read_kv_file, read_lines, read_text, require_linux

# Cap how many processes we report in detail -- a host with thousands of
# processes shouldn't make a single scan slow or the report unreadable.
MAX_PROCESSES = 50


def _pids() -> list[int]:
    return sorted(
        (int(entry) for entry in list_dir("/proc") if entry.isdigit()),
        key=lambda pid: -_rss_kb(pid),
    )[:MAX_PROCESSES]


def _rss_kb(pid: int) -> int:
    status = read_kv_file(f"/proc/{pid}/status")
    value = status.get("VmRSS", "0 kB").split()[0]
    return int(value) if value.isdigit() else 0


def _process_info(pid: int) -> dict[str, Any] | None:
    status = read_kv_file(f"/proc/{pid}/status")
    if not status:
        return None  # process exited between listing and reading -- skip it

    stat_line = (read_text(f"/proc/{pid}/stat") or "").strip()
    # /proc/pid/stat's comm field is in parentheses and may itself contain
    # spaces/parens, so split on the last ')' rather than by whitespace.
    fields_after_comm = stat_line.rsplit(")", 1)[-1].split() if ")" in stat_line else []
    state = fields_after_comm[0] if fields_after_comm else None
    num_threads = int(status.get("Threads", "0") or 0)

    open_fds = len(list_dir(f"/proc/{pid}/fd"))

    return {
        "pid": pid,
        "name": status.get("Name"),
        "state": state,
        "threads": num_threads,
        "vm_rss_kb": int(status.get("VmRSS", "0 kB").split()[0] or 0),
        "vm_size_kb": int(status.get("VmSize", "0 kB").split()[0] or 0),
        "voluntary_ctxt_switches": int(status.get("voluntary_ctxt_switches", "0") or 0),
        "nonvoluntary_ctxt_switches": int(status.get("nonvoluntary_ctxt_switches", "0") or 0),
        "open_fds": open_fds,
    }


@register_collector
class ProcessCollector(Collector):
    name = "process"

    def collect(self) -> dict[str, Any]:
        require_linux()
        all_pids = [e for e in list_dir("/proc") if e.isdigit()]
        processes = []
        for pid in _pids():
            info = _process_info(pid)
            if info is not None:
                processes.append(info)
        return {
            "total_processes": len(all_pids),
            "top_by_rss": processes,
        }
