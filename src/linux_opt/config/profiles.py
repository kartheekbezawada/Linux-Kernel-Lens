"""Loads workload tuning profiles (FR-010's `--profile spark`/`--profile postgres`)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Profiles ship as YAML files under <repo_root>/profiles/<name>.yaml
PROFILES_DIR = Path(__file__).resolve().parents[3] / "profiles"


@dataclass
class Profile:
    name: str
    description: str = ""
    sysctl: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILES_DIR.glob("*.yaml"))


def load_profile(name: str) -> Profile:
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"no profile named {name!r} in {PROFILES_DIR}")
    raw = yaml.safe_load(path.read_text()) or {}
    return Profile(
        name=raw.get("name", name),
        description=raw.get("description", ""),
        sysctl=raw.get("sysctl", {}),
        notes=raw.get("notes", []),
    )
