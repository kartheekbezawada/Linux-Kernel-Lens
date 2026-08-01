"""Simple registry so the CLI can discover collectors without hardcoding imports."""

from __future__ import annotations

from linux_opt.core.base import Collector

_COLLECTORS: dict[str, type[Collector]] = {}


def register_collector(cls: type[Collector]) -> type[Collector]:
    """Class decorator: adds a Collector subclass to the registry keyed by its name."""
    _COLLECTORS[cls.name] = cls
    return cls


def get_collector(name: str) -> type[Collector] | None:
    return _COLLECTORS.get(name)


def all_collectors() -> dict[str, type[Collector]]:
    return dict(_COLLECTORS)
