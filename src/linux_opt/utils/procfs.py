"""Defensive readers for /proc and /sys files.

Collectors read through these instead of raw open() calls so missing files,
permission errors, and non-Linux platforms are handled once instead of in
every collector.
"""

from __future__ import annotations

import platform
from pathlib import Path

from linux_opt.core.exceptions import PermissionDeniedError, UnsupportedPlatformError


def is_linux() -> bool:
    return platform.system() == "Linux"


def require_linux() -> None:
    if not is_linux():
        raise UnsupportedPlatformError(
            f"this operation requires Linux, running on {platform.system()}"
        )


def read_text(path: str | Path) -> str | None:
    """Read a text file, returning None if it doesn't exist.

    Raises PermissionDeniedError on EACCES so callers can distinguish
    "not present" (fine, feature not applicable) from "present but blocked"
    (worth surfacing to the user).
    """
    p = Path(path)
    try:
        return p.read_text(errors="replace")
    except FileNotFoundError:
        return None
    except PermissionError as exc:
        raise PermissionDeniedError(str(p), "permission denied") from exc


def read_lines(path: str | Path) -> list[str]:
    text = read_text(path)
    return text.splitlines() if text is not None else []


def read_int(path: str | Path) -> int | None:
    text = read_text(path)
    if text is None:
        return None
    try:
        return int(text.strip())
    except ValueError:
        return None


def read_kv_file(path: str | Path, sep: str = ":") -> dict[str, str]:
    """Parse files shaped like /proc/meminfo: 'Key:    value unit' per line."""
    result: dict[str, str] = {}
    for line in read_lines(path):
        if sep not in line:
            continue
        key, _, value = line.partition(sep)
        result[key.strip()] = value.strip()
    return result


def list_dir(path: str | Path) -> list[str]:
    p = Path(path)
    try:
        return sorted(entry.name for entry in p.iterdir())
    except FileNotFoundError:
        return []
    except PermissionError as exc:
        raise PermissionDeniedError(str(p), "permission denied") from exc
