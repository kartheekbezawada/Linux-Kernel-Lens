"""Applies a profile's sysctl values (FR-010). Read-only unless explicitly told otherwise.

NFR-Security requires read-only-by-default and explicit confirmation before
any modification, so this module never writes anything itself -- it only
plans changes. The CLI layer is responsible for requiring --apply and, when
not --safe, an interactive confirmation before calling apply_change().
"""

from __future__ import annotations

from dataclasses import dataclass

from linux_opt.config.profiles import Profile
from linux_opt.utils.procfs import read_text, require_linux


@dataclass
class PlannedChange:
    key: str
    current_value: str | None
    desired_value: str
    no_op: bool


def plan_changes(profile: Profile) -> list[PlannedChange]:
    """Read current sysctl values and diff them against the profile. No writes."""
    plans: list[PlannedChange] = []
    for key, desired in profile.sysctl.items():
        path = "/proc/sys/" + key.replace(".", "/")
        current = read_text(path)
        current = current.strip() if current is not None else None
        plans.append(
            PlannedChange(
                key=key,
                current_value=current,
                desired_value=str(desired),
                no_op=(current == str(desired)),
            )
        )
    return plans


def apply_change(change: PlannedChange) -> None:
    """Write one sysctl value. Callers must have already gotten explicit user
    confirmation -- this function does not prompt or check --safe itself."""
    require_linux()
    if change.no_op:
        return
    path = "/proc/sys/" + change.key.replace(".", "/")
    with open(path, "w", encoding="utf-8") as f:
        f.write(change.desired_value)
