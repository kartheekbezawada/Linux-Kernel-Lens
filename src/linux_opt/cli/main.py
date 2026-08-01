"""Entry point for the `linux-opt` CLI."""

from __future__ import annotations

import json
import sys

import click

from linux_opt.core import all_collectors
from linux_opt.core.result import Status
from linux_opt.utils import get_logger

logger = get_logger(__name__)


def _load_collectors() -> None:
    """Import collector packages so their @register_collector decorators run.

    New collectors just need an entry here -- the registry and CLI pick them
    up automatically once imported.
    """
    try:
        import linux_opt.cpu  # noqa: F401
        import linux_opt.disk  # noqa: F401
        import linux_opt.kernel  # noqa: F401
        import linux_opt.memory  # noqa: F401
        import linux_opt.network  # noqa: F401
        import linux_opt.numa  # noqa: F401
        import linux_opt.scheduler  # noqa: F401
    except ImportError:
        pass


@click.group()
def cli() -> None:
    """linux-opt: Linux hardware/OS discovery, performance analysis, and tuning."""


@cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "text"]),
    default="text",
    help="Output format for scan results.",
)
def scan(output_format: str) -> None:
    """Run every registered collector and print what it found."""
    _load_collectors()
    collectors = all_collectors()
    if not collectors:
        click.echo("No collectors registered yet.", err=True)
        sys.exit(1)

    results = {name: cls().run() for name, cls in collectors.items()}

    if output_format == "json":
        payload = {
            name: {"status": r.status.value, "data": r.data, "errors": r.errors}
            for name, r in results.items()
        }
        click.echo(json.dumps(payload, indent=2, default=str))
        return

    for name, result in results.items():
        marker = "OK" if result.status == Status.OK else result.status.value.upper()
        click.echo(f"[{marker}] {name}")
        for err in result.errors:
            click.echo(f"    error: {err}")


@cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "text"]),
    default="text",
    help="Output format for the recommendation report.",
)
def analyze(output_format: str) -> None:
    """Collect system data and print ranked recommendations (FR-009 format)."""
    _load_collectors()

    from linux_opt.recommendations import generate_recommendations

    _results, recommendations = generate_recommendations()

    if output_format == "json":
        payload = [
            {
                "severity": r.severity.value,
                "problem": r.problem,
                "evidence": r.evidence,
                "recommendation": r.recommendation,
                "expected_improvement": r.expected_improvement,
                "source": r.source,
            }
            for r in recommendations
        ]
        click.echo(json.dumps(payload, indent=2))
        return

    if not recommendations:
        click.echo("No issues found.")
        return

    for r in recommendations:
        click.echo(f"Severity: {r.severity.value.upper()}")
        click.echo(f"Problem: {r.problem}")
        click.echo(f"Evidence: {r.evidence}")
        click.echo(f"Recommendation: {r.recommendation}")
        if r.expected_improvement:
            click.echo(f"Expected Improvement: {r.expected_improvement}")
        click.echo("")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
