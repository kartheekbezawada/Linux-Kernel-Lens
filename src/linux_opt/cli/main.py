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


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
