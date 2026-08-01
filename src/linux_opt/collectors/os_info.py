"""OS/distro discovery collector (FR-002).

Package managers and init systems vary across distros (FR's portability
target list: Ubuntu/Debian/RHEL/Rocky/AlmaLinux/SUSE/Fedora), so this
collector probes for whichever tools exist via shutil.which() rather than
assuming one package manager or init system is present.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Any

from linux_opt.core.base import Collector
from linux_opt.core.registry import register_collector
from linux_opt.utils.procfs import read_text, require_linux

SUBPROCESS_TIMEOUT_S = 5


def _run(cmd: list[str]) -> str | None:
    """Run a command and return its stdout, or None if it's missing/fails/times out.

    Never raises -- OS discovery is best-effort and one missing tool
    shouldn't fail the whole collector.
    """
    if shutil.which(cmd[0]) is None:
        return None
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_S, check=False
        )
        return result.stdout if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _os_release() -> dict[str, str]:
    """Parse /etc/os-release, which is the standard distro-identification file
    across all of this project's target distros."""
    raw = read_text("/etc/os-release") or ""
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        parsed[key.strip()] = value.strip().strip('"')
    return parsed


def _boot_params() -> str:
    return (read_text("/proc/cmdline") or "").strip()


def _package_count() -> dict[str, int]:
    """Try each known package manager; only the one present on this distro will return a count."""
    counts: dict[str, int] = {}
    dpkg_out = _run(["dpkg-query", "-f", ".\n", "-W"])
    if dpkg_out is not None:
        counts["dpkg"] = len(dpkg_out.splitlines())
    rpm_out = _run(["rpm", "-qa"])
    if rpm_out is not None:
        counts["rpm"] = len(rpm_out.splitlines())
    return counts


def _running_services() -> list[str]:
    """List active systemd services, if systemd is the init system."""
    out = _run(
        ["systemctl", "list-units", "--type=service", "--state=running", "--no-legend", "--plain"]
    )
    if out is None:
        return []
    return [line.split()[0] for line in out.splitlines() if line.strip()]


@register_collector
class OsInfoCollector(Collector):
    name = "os_info"

    def collect(self) -> dict[str, Any]:
        require_linux()
        os_release = _os_release()
        return {
            "distro": os_release.get("PRETTY_NAME") or os_release.get("NAME"),
            "distro_id": os_release.get("ID"),
            "kernel_release": platform.release(),
            "boot_params": _boot_params(),
            "package_counts": _package_count(),
            "running_services": _running_services(),
        }
