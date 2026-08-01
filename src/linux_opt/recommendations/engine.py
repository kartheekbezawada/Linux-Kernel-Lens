"""Orchestrates collectors and analyzers into a single ranked recommendation list (FR-009)."""

from __future__ import annotations

from linux_opt.core.registry import all_analyzers, all_collectors
from linux_opt.core.result import CollectionResult, Recommendation, Severity

_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


def run_collectors() -> dict[str, CollectionResult]:
    """Run every registered collector and return its result keyed by name."""
    return {name: cls().run() for name, cls in all_collectors().items()}


def run_analyzers(results: dict[str, CollectionResult]) -> list[Recommendation]:
    """Run every registered analyzer against the given collector results."""
    recommendations: list[Recommendation] = []
    for cls in all_analyzers().values():
        recommendations.extend(cls().analyze(results))
    return recommendations


def generate_recommendations() -> tuple[dict[str, CollectionResult], list[Recommendation]]:
    """End-to-end entry point: collect, analyze, and rank by severity.

    Returns both the raw collector results (for reporting) and the sorted
    recommendation list, so callers don't need to re-run collectors.
    """
    results = run_collectors()
    recommendations = run_analyzers(results)
    recommendations.sort(key=lambda r: _SEVERITY_ORDER.get(r.severity, 99))
    return results, recommendations
