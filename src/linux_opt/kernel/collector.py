"""Sysctl and kernel version collector (FR-002, FR-008)."""

from __future__ import annotations

import platform
from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import read_text, require_linux

# A focused set of sysctls worth reading by default across vm/net/fs/kernel
# namespaces (FR-008). Full traversal of /proc/sys is possible but noisy;
# these are the keys the analyzer in this same package actually checks.
SYSCTL_KEYS = [
    "vm.swappiness",
    "vm.dirty_ratio",
    "vm.dirty_background_ratio",
    "vm.overcommit_memory",
    "vm.min_free_kbytes",
    "net.core.somaxconn",
    "net.ipv4.tcp_max_syn_backlog",
    "net.ipv4.tcp_tw_reuse",
    "net.core.rmem_max",
    "net.core.wmem_max",
    "fs.file-max",
    "kernel.pid_max",
    "kernel.threads-max",
    "kernel.numa_balancing",
]


def _sysctl_path(key: str) -> str:
    return "/proc/sys/" + key.replace(".", "/")


def _read_sysctl(key: str) -> str | None:
    text = read_text(_sysctl_path(key))
    return text.strip() if text is not None else None


def _kernel_version() -> dict[str, str]:
    return {
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }


@register_collector
class KernelCollector(Collector):
    name = "kernel"

    def collect(self) -> dict[str, Any]:
        require_linux()
        sysctls = {key: _read_sysctl(key) for key in SYSCTL_KEYS}
        return {
            "kernel": _kernel_version(),
            "sysctl": {k: v for k, v in sysctls.items() if v is not None},
        }
