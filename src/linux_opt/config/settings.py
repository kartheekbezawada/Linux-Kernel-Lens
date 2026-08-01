"""User-level config file: read-only mode, default output format, etc.

Read-only-by-default is a security requirement (NFR-Security), not just a
convenience default, so the loader always sets it unless a config file
explicitly opts out.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATHS = [
    Path.home() / ".config" / "linux-opt" / "config.yaml",
    Path.cwd() / "linux-opt.yaml",
]


@dataclass
class Settings:
    read_only: bool = True
    default_format: str = "text"


def load_settings(explicit_path: str | None = None) -> Settings:
    paths = [Path(explicit_path)] if explicit_path else DEFAULT_CONFIG_PATHS
    for path in paths:
        if path.is_file():
            raw = yaml.safe_load(path.read_text()) or {}
            return Settings(
                read_only=raw.get("read_only", True),
                default_format=raw.get("default_format", "text"),
            )
    return Settings()
