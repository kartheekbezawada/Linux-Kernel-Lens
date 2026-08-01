"""Simple registries so the CLI can discover collectors/analyzers without hardcoding imports."""

from __future__ import annotations

from linux_opt.core.base import Analyzer, Collector

_COLLECTORS: dict[str, type[Collector]] = {}
_ANALYZERS: dict[str, type[Analyzer]] = {}


def register_collector(cls: type[Collector]) -> type[Collector]:
    """Class decorator: adds a Collector subclass to the registry keyed by its name."""
    _COLLECTORS[cls.name] = cls
    return cls


def get_collector(name: str) -> type[Collector] | None:
    return _COLLECTORS.get(name)


def all_collectors() -> dict[str, type[Collector]]:
    return dict(_COLLECTORS)


def register_analyzer(cls: type[Analyzer]) -> type[Analyzer]:
    """Class decorator: adds an Analyzer subclass to the registry keyed by its name."""
    _ANALYZERS[cls.name] = cls
    return cls


def get_analyzer(name: str) -> type[Analyzer] | None:
    return _ANALYZERS.get(name)


def all_analyzers() -> dict[str, type[Analyzer]]:
    return dict(_ANALYZERS)
