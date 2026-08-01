"""Base class and registry for workload plugins (FR-007 / requirements.md section 7).

A Plugin bundles what a Collector+Analyzer pair does, but scoped to one
workload (Postgres, Redis, Kafka, etc.) and gated by detect() -- unlike
core collectors, which always run, a plugin should only collect/analyze
when its workload is actually present on the host. Plugins live in their
own registry (not core's collector/analyzer registries) because they're
opt-in and workload-specific rather than always-on system discovery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from linux_opt.core.result import Recommendation

_PLUGINS: dict[str, type["Plugin"]] = {}


class Plugin(ABC):
    name: str = "plugin"

    @abstractmethod
    def detect(self) -> bool:
        """Return True if this workload is present/running on the host.

        Must be cheap and side-effect-free -- called on every host even
        when the workload isn't there, so it shouldn't do expensive work.
        """

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """Gather workload-specific metrics. Only called after detect() is True."""

    @abstractmethod
    def analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        """Turn this plugin's own collected data into recommendations."""

    def run(self) -> list[Recommendation]:
        """Detect, collect, and analyze in one call. Returns [] if not detected
        or if collection fails -- a broken plugin shouldn't break the scan."""
        try:
            if not self.detect():
                return []
            data = self.collect()
            return self.analyze(data)
        except Exception:  # noqa: BLE001 - a plugin failure must never crash the scan
            return []


def register_plugin(cls: type[Plugin]) -> type[Plugin]:
    _PLUGINS[cls.name] = cls
    return cls


def get_plugin(name: str) -> type[Plugin] | None:
    return _PLUGINS.get(name)


def all_plugins() -> dict[str, type[Plugin]]:
    return dict(_PLUGINS)
