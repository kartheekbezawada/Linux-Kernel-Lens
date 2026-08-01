"""Abstract base classes that every collector and analyzer implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from linux_opt.core.result import CollectionResult, Recommendation, Status


class Collector(ABC):
    """Reads raw data from the OS (procfs/sysfs/CLI tools). Never writes anything."""

    #: short identifier used in reports and logs, e.g. "cpu", "numa"
    name: str = "collector"

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """Gather raw data. Implementations should raise CollectionError on failure."""

    def run(self) -> CollectionResult:
        """Wraps collect() in a uniform, never-throwing envelope."""
        try:
            data = self.collect()
            return CollectionResult(source=self.name, status=Status.OK, data=data)
        except Exception as exc:  # noqa: BLE001 - a bad collector shouldn't kill the scan
            return CollectionResult(
                source=self.name, status=Status.FAILED, errors=[str(exc)]
            )


class Analyzer(ABC):
    """Turns one or more CollectionResults into Recommendations."""

    name: str = "analyzer"

    @abstractmethod
    def analyze(self, results: dict[str, CollectionResult]) -> list[Recommendation]:
        """Inspect collected data and return zero or more recommendations."""
