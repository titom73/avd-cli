#!/usr/bin/env python
# coding: utf-8 -*-

"""Main CLI entry point for AVD CLI.

This module defines the main CLI group and command structure using Click.
"""

import sys
from pathlib import Path
from typing import Optional
from typing import Any, Callable

import click
from rich.console import Console

from avd_cli import __version__
from avd_cli.constants import APP_NAME
from avd_cli.utils.version import get_pyavd_version
from avd_cli.cli.commands.deploy import deploy as deploy_cmd
from avd_cli.cli.commands.generate import generate as generate_cmd
from avd_cli.cli.commands.pyavd import pyavd_cmd

# Initialize Rich console for beautiful output
console = Console()


def version_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Display version information for avd-cli and pyavd.

    Parameters
    ----------
    ctx : click.Context
        The Click context.
    param : click.Parameter
        The Click parameter.
    value : bool
        Whether the option was provided.
    """
    if not value or ctx.resilient_parsing:
        return

    pyavd_version = get_pyavd_version()
    click.echo(f"{APP_NAME}, version {__version__}")
    click.echo(f"pyavd, version {pyavd_version}")
    ctx.exit()


def suppress_pyavd_warnings(show_warnings: bool) -> None:
    """Suppress pyavd deprecation warnings unless explicitly requested.

    Parameters
    ----------
    show_warnings : bool
        If False, suppress deprecation warnings from pyavd
    """
    if not show_warnings:
        import warnings

        warnings.filterwarnings("ignore", message=".*is deprecated.*", category=UserWarning)


def resolve_output_path(inventory_path: Path, output_path: Optional[Path]) -> Path:
    """Resolve the output path, applying default if needed.

    Parameters
    ----------
    inventory_path : Path
        Path to the inventory directory
    output_path : Optional[Path]
        User-provided output path, or None to use default

    Returns
    -------
    Path
        Resolved output path (defaults to <inventory_path>/intended)
    """
    if output_path is None:
        output_path = inventory_path / "intended"
        console.print(f"[blue]ℹ[/blue] Using default output path: {output_path}")
    return output_path


def display_generation_summary(category: str, count: int, output_path: Path, subcategory: str = "configs") -> None:
    """Display a summary table for generated files.

    Parameters
    ----------
    category : str
        Category of generated files (e.g., "Configurations", "Documentation")
    count : int
        Number of files generated
    subcategory : str, optional
        Subdirectory name under output_path, by default "configs"
    """
    from rich.table import Table

    table = Table(title="Generated Files")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Output Path", style="green")

    table.add_row(category, str(count), str(output_path / subcategory))

    console.print("\n")
    console.print(table)


@click.group()
@click.option(
    "--version",
    is_flag=True,
    callback=version_callback,
    expose_value=False,
    is_eager=True,
    help="Show version information for avd-cli and pyavd.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output for debugging",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """AVD CLI - Process Arista AVD inventories and generate configurations.

    This tool processes Arista Ansible AVD inventories using py-avd to generate:
    - Device configurations
    - Documentation
    - ANTA tests

    Examples
    --------
    Generate all outputs (configs, docs, tests):

        $ avd-cli generate all -i ./inventory -o ./output

    Generate only configurations:

        $ avd-cli generate configs -i ./inventory -o ./output

    Generate for specific groups:

        $ avd-cli generate all -i ./inventory -o ./output -l spine -l leaf

    Display inventory information:

        $ avd-cli info -i ./inventory

    For more information on each command or command group:

        $ avd-cli COMMAND --help
        $ avd-cli generate --help
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["verbose"] = verbose

    # Configure logging level based on verbose flag
    if verbose:
        console.print("[blue]ℹ[/blue] Verbose mode enabled", style="dim")


# Common options decorator for generate subcommands
def common_generate_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Apply common options to all generate subcommands.

    All options support environment variables with the prefix AVD_CLI_.
    Environment variables are automatically shown in --help output.
    Command-line arguments take precedence over environment variables.
    """
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
        hidden=True,  # Hide from help but keep for backward compatibility
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


@cli.command()
@click.option(
    "--inventory-path",
    "-i",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    envvar="AVD_CLI_INVENTORY_PATH",
    show_envvar=True,
    help="Path to AVD inventory directory",
)
@click.pass_context
def validate(ctx: click.Context, inventory_path: Path) -> None:
    """Validate AVD inventory structure and data.

    This command validates the inventory structure, YAML syntax, and data integrity
    without generating any output files.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Examples
    --------
    Validate inventory structure:

        $ avd-cli validate -i ./inventory

    Using environment variables:

        $ export AVD_CLI_INVENTORY_PATH=./inventory
        $ avd-cli validate
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Validating inventory at: {inventory_path}")

    try:
        from avd_cli.logics.loader import InventoryLoader

        # Load inventory
        console.print("[cyan]→[/cyan] Loading and validating inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        # Validate inventory
        errors = inventory.validate()

        if errors:
            console.print(f"\n[red]✗[/red] Validation failed with {len(errors)} error(s):")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)
        else:
            console.print("\n[green]✓[/green] Validation successful!")
            device_count = len(inventory.get_all_devices())
            fabric_count = len(inventory.fabrics)
            console.print(f"[green]→[/green] Found {device_count} devices in {fabric_count} fabric(s)")

            # Display summary
            for fabric in inventory.fabrics:
                console.print(f"\n[cyan]Fabric:[/cyan] {fabric.name}")
                console.print(f"  Spines: {len(fabric.spine_devices)}")
                console.print(f"  Leaves: {len(fabric.leaf_devices)}")
                if fabric.border_leaf_devices:
                    console.print(f"  Border Leaves: {len(fabric.border_leaf_devices)}")

    except Exception as e:
        console.print(f"[red]✗[/red] Validation error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--inventory-path",
    "-i",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    envvar="AVD_CLI_INVENTORY_PATH",
    show_envvar=True,
    help="Path to AVD inventory directory",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"], case_sensitive=False),
    default="table",
    envvar="AVD_CLI_FORMAT",
    show_envvar=True,
    help="Output format for inventory information",
)
@click.pass_context
def info(ctx: click.Context, inventory_path: Path, format: str) -> None:  # noqa: C901
    """Display inventory information and statistics.

    This command analyzes the inventory and displays information about
    devices, groups, and fabric structure.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Examples
    --------
    Display inventory info as table:

        $ avd-cli info -i ./inventory

    Display inventory info as JSON:

        $ avd-cli info -i ./inventory --format json

    Using environment variables:

        $ export AVD_CLI_INVENTORY_PATH=./inventory
        $ export AVD_CLI_FORMAT=json
        $ avd-cli info
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Reading inventory from: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output format: {format}")

    try:
        import json

        from rich.table import Table

        from avd_cli.logics.loader import InventoryLoader

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        total_devices = len(inventory.get_all_devices())
        console.print(f"[green]✓[/green] Loaded {total_devices} devices\n")

        if format == "table":
            # Display as formatted table
            table = Table(title="Inventory Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Devices", str(total_devices))
            table.add_row("Total Fabrics", str(len(inventory.fabrics)))

            for fabric in inventory.fabrics:
                table.add_row(f"Fabric: {fabric.name}", "")
                table.add_row("  - Design Type", fabric.design_type)
                table.add_row("  - Spine Devices", str(len(fabric.spine_devices)))
                table.add_row("  - Leaf Devices", str(len(fabric.leaf_devices)))
                table.add_row("  - Border Leaf Devices", str(len(fabric.border_leaf_devices)))

            console.print(table)

            # Device details table
            if total_devices > 0:
                console.print("\n")
                device_table = Table(title="Devices")
                device_table.add_column("Hostname", style="cyan")
                device_table.add_column("Type", style="yellow")
                device_table.add_column("Platform", style="magenta")
                device_table.add_column("Management IP", style="green")
                device_table.add_column("Fabric", style="blue")

                for device in sorted(inventory.get_all_devices(), key=lambda d: d.hostname):
                    device_table.add_row(
                        device.hostname,
                        device.device_type,
                        device.platform,
                        str(device.mgmt_ip),
                        device.fabric,
                    )

                console.print(device_table)

        elif format == "json":
            # Display as JSON
            from typing import Dict as DictType
            from typing import List as ListType

            info_data: DictType[str, Any] = {
                "total_devices": total_devices,
                "total_fabrics": len(inventory.fabrics),
                "fabrics": [],
            }
            fabrics_list: ListType[DictType[str, Any]] = []

            for fabric in inventory.fabrics:
                fabric_data: DictType[str, Any] = {
                    "name": fabric.name,
                    "design_type": fabric.design_type,
                    "spine_devices": len(fabric.spine_devices),
                    "leaf_devices": len(fabric.leaf_devices),
                    "border_leaf_devices": len(fabric.border_leaf_devices),
                    "devices": [
                        {
                            "hostname": d.hostname,
                            "type": d.device_type,
                            "platform": d.platform,
                            "mgmt_ip": str(d.mgmt_ip),
                        }
                        for d in fabric.get_all_devices()
                    ],
                }
                fabrics_list.append(fabric_data)

            info_data["fabrics"] = fabrics_list

            console.print_json(json.dumps(info_data, indent=2))

        elif format == "yaml":
            # Display as YAML
            from typing import Dict as DictType
            from typing import List as ListType

            import yaml as yaml_lib

            yaml_info_data: DictType[str, Any] = {
                "total_devices": total_devices,
                "total_fabrics": len(inventory.fabrics),
                "fabrics": [],
            }
            yaml_fabrics_list: ListType[DictType[str, Any]] = []

            for fabric in inventory.fabrics:
                yaml_fabric_data: DictType[str, Any] = {
                    "name": fabric.name,
                    "design_type": fabric.design_type,
                    "spine_devices": len(fabric.spine_devices),
                    "leaf_devices": len(fabric.leaf_devices),
                    "border_leaf_devices": len(fabric.border_leaf_devices),
                    "devices": [
                        {
                            "hostname": d.hostname,
                            "type": d.device_type,
                            "platform": d.platform,
                            "mgmt_ip": str(d.mgmt_ip),
                        }
                        for d in fabric.get_all_devices()
                    ],
                }
                yaml_fabrics_list.append(yaml_fabric_data)

            yaml_info_data["fabrics"] = yaml_fabrics_list

            console.print(yaml_lib.dump(yaml_info_data, default_flow_style=False))

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


# Register command groups from commands module
cli.add_command(deploy_cmd, name="deploy")
cli.add_command(generate_cmd, name="generate")
cli.add_command(pyavd_cmd, name="pyavd")


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            console.print_exception(show_locals=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
