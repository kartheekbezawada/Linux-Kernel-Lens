"""Structured result types returned by every collector and analyzer."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass
class CollectionResult:
    """Uniform envelope for data returned by a Collector.run()."""

    source: str
    status: Status
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def ok(self) -> bool:
        return self.status in (Status.OK, Status.PARTIAL)


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Recommendation:
    """A single actionable finding: what's wrong, the evidence, and the fix."""

    severity: Severity
    problem: str
    evidence: str
    recommendation: str
    expected_improvement: str | None = None
    source: str | None = None
