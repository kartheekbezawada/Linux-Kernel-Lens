"""Render collector results and recommendations into report formats (FR-012).

PDF is left for a follow-up -- it needs a heavier dependency
(weasyprint/reportlab) than this pass wants to pull in.
"""

from __future__ import annotations

import csv
import html
import io
import json

import yaml

from linux_opt.core.result import CollectionResult, Recommendation
from linux_opt.reporting.pdf import build_pdf

# Severity -> CSS class, used by render_html for color-coding rows.
_SEVERITY_CLASS = {"critical": "sev-critical", "high": "sev-high", "medium": "sev-medium", "low": "sev-low"}


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


def render_html(results: dict[str, CollectionResult], recommendations: list[Recommendation]) -> str:
    # All user/system-derived strings go through html.escape() before landing
    # in markup -- collector data ultimately comes from the machine being
    # scanned (process names, distro strings, etc.), so it's untrusted input.
    rows = []
    for r in recommendations:
        css_class = _SEVERITY_CLASS.get(r.severity.value, "")
        improvement = f"<td>{html.escape(r.expected_improvement)}</td>" if r.expected_improvement else "<td>-</td>"
        rows.append(
            f"<tr class='{css_class}'>"
            f"<td>{html.escape(r.severity.value.upper())}</td>"
            f"<td>{html.escape(r.problem)}</td>"
            f"<td>{html.escape(r.evidence)}</td>"
            f"<td>{html.escape(r.recommendation)}</td>"
            f"{improvement}"
            "</tr>"
        )
    recommendations_table = (
        "<table><thead><tr><th>Severity</th><th>Problem</th><th>Evidence</th>"
        "<th>Recommendation</th><th>Expected Improvement</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        if recommendations
        else "<p>No issues found.</p>"
    )

    collector_rows = "".join(
        f"<li><strong>{html.escape(name)}</strong>: {html.escape(result.status.value)}"
        + ("".join(f"<br><small>error: {html.escape(e)}</small>" for e in result.errors))
        + "</li>"
        for name, result in results.items()
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Linux Kernel Lens Report</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
.sev-critical, .sev-high {{ background: #fde2e2; }}
.sev-medium {{ background: #fff4d6; }}
.sev-low {{ background: #eef; }}
</style></head>
<body>
<h1>Linux Kernel Lens Report</h1>
<h2>Collectors</h2>
<ul>{collector_rows}</ul>
<h2>Recommendations</h2>
{recommendations_table}
</body></html>
"""


def render_pdf(results: dict[str, CollectionResult], recommendations: list[Recommendation]) -> bytes:
    """Returns bytes, unlike every other renderer here -- PDF is a binary
    format. Callers (the CLI) need to write it with a binary file handle."""
    lines = ["Linux Kernel Lens Report", "", "Collectors:"]
    for name, result in results.items():
        lines.append(f"  {name}: {result.status.value}")
        for err in result.errors:
            lines.append(f"    error: {err}")

    lines += ["", "Recommendations:", ""]
    if not recommendations:
        lines.append("No issues found.")
    for r in recommendations:
        lines.append(f"Severity: {r.severity.value.upper()}")
        lines.append(f"Problem: {r.problem}")
        lines.append(f"Evidence: {r.evidence}")
        lines.append(f"Recommendation: {r.recommendation}")
        if r.expected_improvement:
            lines.append(f"Expected Improvement: {r.expected_improvement}")
        lines.append("")

    return build_pdf(lines)


# PDF is binary, so it's kept out of RENDERERS (which all return str) and
# handled separately by callers that check for the "pdf" format explicitly.
RENDERERS = {
    "json": render_json,
    "yaml": render_yaml,
    "markdown": render_markdown,
    "csv": render_csv,
    "html": render_html,
}


def render(
    output_format: str, results: dict[str, CollectionResult], recommendations: list[Recommendation]
) -> str:
    try:
        renderer = RENDERERS[output_format]
    except KeyError as exc:
        raise ValueError(f"unsupported report format: {output_format!r}") from exc
    return renderer(results, recommendations)
