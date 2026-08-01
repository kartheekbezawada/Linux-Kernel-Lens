"""Render collector results and recommendations into report formats (FR-012).

HTML/PDF are left for a follow-up -- JSON/YAML/Markdown/CSV cover the
structured and human-readable cases with no extra dependencies beyond
PyYAML, which is already a project dependency.
"""

from __future__ import annotations

import csv
import io
import json

import yaml

from linux_opt.core.result import CollectionResult, Recommendation


def _to_plain(results: dict[str, CollectionResult], recommendations: list[Recommendation]) -> dict:
    return {
        "collectors": {
            name: {"status": r.status.value, "data": r.data, "errors": r.errors}
            for name, r in results.items()
        },
        "recommendations": [
            {
                "severity": r.severity.value,
                "problem": r.problem,
                "evidence": r.evidence,
                "recommendation": r.recommendation,
                "expected_improvement": r.expected_improvement,
                "source": r.source,
            }
            for r in recommendations
        ],
    }


def render_json(results: dict[str, CollectionResult], recommendations: list[Recommendation]) -> str:
    return json.dumps(_to_plain(results, recommendations), indent=2, default=str)


def render_yaml(results: dict[str, CollectionResult], recommendations: list[Recommendation]) -> str:
    return yaml.safe_dump(_to_plain(results, recommendations), sort_keys=False)


def render_markdown(results: dict[str, CollectionResult], recommendations: list[Recommendation]) -> str:
    lines = ["# Linux Kernel Lens Report", "", "## Collectors", ""]
    for name, result in results.items():
        lines.append(f"- **{name}**: {result.status.value}")
        for err in result.errors:
            lines.append(f"  - error: {err}")

    lines += ["", "## Recommendations", ""]
    if not recommendations:
        lines.append("No issues found.")
    for r in recommendations:
        lines += [
            f"### {r.problem}",
            f"- **Severity:** {r.severity.value}",
            f"- **Evidence:** {r.evidence}",
            f"- **Recommendation:** {r.recommendation}",
        ]
        if r.expected_improvement:
            lines.append(f"- **Expected Improvement:** {r.expected_improvement}")
        lines.append("")
    return "\n".join(lines)


def render_csv(results: dict[str, CollectionResult], recommendations: list[Recommendation]) -> str:
    """Recommendations only -- collector output doesn't fit a flat row shape."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["severity", "problem", "evidence", "recommendation", "expected_improvement", "source"])
    for r in recommendations:
        writer.writerow(
            [r.severity.value, r.problem, r.evidence, r.recommendation, r.expected_improvement or "", r.source or ""]
        )
    return buffer.getvalue()


RENDERERS = {
    "json": render_json,
    "yaml": render_yaml,
    "markdown": render_markdown,
    "csv": render_csv,
}


def render(
    output_format: str, results: dict[str, CollectionResult], recommendations: list[Recommendation]
) -> str:
    try:
        renderer = RENDERERS[output_format]
    except KeyError as exc:
        raise ValueError(f"unsupported report format: {output_format!r}") from exc
    return renderer(results, recommendations)
