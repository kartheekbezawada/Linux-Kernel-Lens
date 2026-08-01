"""Unit tests for core/registry.py's collector/analyzer registration."""

from __future__ import annotations

from linux_opt.core.base import Analyzer, Collector
from linux_opt.core.registry import (
    all_analyzers,
    all_collectors,
    get_analyzer,
    get_collector,
    register_analyzer,
    register_collector,
)


def test_register_collector_adds_to_registry():
    @register_collector
    class _TestOnlyCollector(Collector):
        name = "test_only_collector_xyz"

        def collect(self) -> dict:
            return {}

    assert get_collector("test_only_collector_xyz") is _TestOnlyCollector
    assert "test_only_collector_xyz" in all_collectors()


def test_get_collector_returns_none_for_unknown_name():
    assert get_collector("definitely_not_registered_abc123") is None


def test_register_analyzer_adds_to_registry():
    @register_analyzer
    class _TestOnlyAnalyzer(Analyzer):
        name = "test_only_analyzer_xyz"

        def analyze(self, results: dict) -> list:
            return []

    assert get_analyzer("test_only_analyzer_xyz") is _TestOnlyAnalyzer
    assert "test_only_analyzer_xyz" in all_analyzers()


def test_all_collectors_returns_a_copy_not_the_live_registry():
    snapshot = all_collectors()
    snapshot["injected_fake_entry"] = object()
    assert "injected_fake_entry" not in all_collectors()
