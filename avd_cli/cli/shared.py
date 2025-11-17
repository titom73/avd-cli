from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Optional

import click
from rich.console import Console
from rich.table import Table

from avd_cli import __version__
from avd_cli.constants import APP_NAME

console = Console()


def suppress_pyavd_warnings(show_warnings: bool) -> None:
    """Suppress PyAVD deprecation warnings unless explicitly requested."""

    if show_warnings:
        return

    import warnings

    warnings.filterwarnings("ignore", message=".*is deprecated.*", category=UserWarning)


def resolve_output_path(inventory_path: Path, output_path: Optional[Path]) -> Path:
    """Resolve the output path, defaulting to <inventory>/intended when missing."""

    if output_path is None:
        output_path = inventory_path / "intended"
        console.print(f"[blue]ℹ[/blue] Using default output path: {output_path}")
    return output_path


def display_generation_summary(category: str, count: int, output_path: Path, subcategory: str = "configs") -> None:
    """Render a short summary table describing generated assets."""

    table = Table(title="Generated Files")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Output Path", style="green")

    table.add_row(category, str(count), str(output_path / subcategory))

    console.print("\n")
    console.print(table)


def common_generate_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate generate subcommands with consistency options."""

    func = click.option(
        "--inventory-path",
        "-i",
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        required=True,
        envvar="AVD_CLI_INVENTORY_PATH",
        show_envvar=True,
        help="Path to AVD inventory directory",
    )(func)
    func = click.option(
        "--output-path",
        "-o",
        type=click.Path(path_type=Path),
        default=None,
        envvar="AVD_CLI_OUTPUT_PATH",
        show_envvar=True,
        help="Output directory for generated files (default: <inventory_path>/intended)",
    )(func)
    func = click.option(
        "--limit",
        "-l",
        "limit_patterns",
        multiple=True,
        envvar="AVD_CLI_LIMIT",
        show_envvar=True,
        help=(
            "Filter devices by hostname or group name pattern. "
            "Supports glob wildcards: *, ?, [...]. "
            "Can be specified multiple times for union. "
            "Example: --limit 'leaf-*' --limit spine-1"
        ),
    )(func)
    func = click.option(
        "--limit-to-groups",
        "limit_to_groups_patterns",
        multiple=True,
        envvar="AVD_CLI_LIMIT_TO_GROUPS",
        show_envvar=True,
        hidden=True,
        help="(Deprecated: use --limit instead) Filter devices by group name pattern",
    )(func)
    func = click.option(
        "--show-deprecation-warnings",
        is_flag=True,
        default=False,
        envvar="AVD_CLI_SHOW_DEPRECATION_WARNINGS",
        show_envvar=True,
        help="Show pyavd deprecation warnings (hidden by default)",
    )(func)
    func = click.pass_context(func)
    return func


def main_cli() -> click.Group:
    """Create the top-level Click group so subcommands can register against it."""

    @click.group()
    @click.version_option(__version__, prog_name=APP_NAME)
    @click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose output for debugging",
    )
    @click.pass_context
    def cli(ctx: click.Context, verbose: bool) -> None:
        ctx.ensure_object(dict)
        ctx.obj["verbose"] = verbose
        if verbose:
            console.print("[blue]ℹ[/blue] Verbose mode enabled", style="dim")

    return cli


def run_cli(cli_group: click.Group) -> None:
    """Invoke the CLI, bubbling up any uncaught exceptions."""

    try:
        cli_group(obj={})
    except Exception as exc:
        console.print(f"[red]✗[/red] Error: {exc}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            console.print_exception(show_locals=True)
        sys.exit(1)
