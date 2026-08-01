"""Unit tests for core/base.py's Collector.run() never-crash contract."""

from __future__ import annotations

from linux_opt.core.base import Analyzer, Collector
from linux_opt.core.result import Recommendation, Severity, Status


class _WorkingCollector(Collector):
    name = "working"

    def collect(self) -> dict:
        return {"key": "value"}


class _FailingCollector(Collector):
    name = "failing"

    def collect(self) -> dict:
        raise RuntimeError("simulated collection failure")


class _EchoAnalyzer(Analyzer):
    name = "echo"

    def analyze(self, results: dict) -> list[Recommendation]:
        return [
            Recommendation(severity=Severity.LOW, problem="p", evidence="e", recommendation="r")
            for _ in results
        ]


def test_working_collector_returns_ok_status():
    result = _WorkingCollector().run()
    assert result.status == Status.OK
    assert result.data == {"key": "value"}
    assert result.errors == []
    assert result.ok is True


def test_failing_collector_returns_failed_status_not_exception():
    # The whole point of Collector.run() is that a broken collect() can't
    # crash a scan -- this is the contract every other collector relies on.
    result = _FailingCollector().run()
    assert result.status == Status.FAILED
    assert "simulated collection failure" in result.errors[0]
    assert result.ok is False


def test_analyzer_receives_full_results_dict():
    results = {"a": _WorkingCollector().run(), "b": _FailingCollector().run()}
    recommendations = _EchoAnalyzer().analyze(results)
    assert len(recommendations) == 2
