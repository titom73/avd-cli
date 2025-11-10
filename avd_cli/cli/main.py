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

# Initialize Rich console for beautiful output
console = Console()


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
@click.version_option(version=__version__, prog_name=APP_NAME)
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
        "--limit-to-groups",
        "-l",
        multiple=True,
        envvar="AVD_CLI_LIMIT_TO_GROUPS",
        show_envvar=True,
        help="Limit processing to specific groups (can be used multiple times). "
        "Use comma-separated values in environment variable",
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


@cli.group()
@click.pass_context
def generate(ctx: click.Context) -> None:
    """Generate configurations, documentation, and tests from AVD inventory.

    This command group provides subcommands for generating different types
    of outputs from Arista AVD inventories.

    Examples
    --------
    Generate all outputs (uses default output path ./inventory/intended):

        $ avd-cli generate all -i ./inventory

    Generate all outputs with custom path:

        $ avd-cli generate all -i ./inventory -o ./custom-output

    Generate only configurations:

        $ avd-cli generate configs -i ./inventory

    Generate only ANTA tests with custom output:

        $ avd-cli generate tests -i ./inventory -o ./tests
    """
    pass


@generate.command("all")
@common_generate_options
@click.option(
    "--workflow",
    type=click.Choice(["eos-design", "cli-config", "full", "config-only"], case_sensitive=False),
    default="eos-design",
    envvar="AVD_CLI_WORKFLOW",
    show_envvar=True,
    help=(
        "Workflow type: eos-design (eos_design + eos_cli_config_gen) or cli-config (eos_cli_config_gen only). "
        "Legacy values 'full' and 'config-only' are deprecated."
    ),
)
def generate_all(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple[str, ...],
    show_deprecation_warnings: bool,
    workflow: str,
) -> None:
    """Generate all outputs: configurations, documentation, and tests.

    This command generates everything from the AVD inventory:
    - Device configurations
    - Documentation
    - ANTA test files

    If --output-path is not specified, outputs are written to <inventory_path>/intended/

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Examples
    --------
    Generate all outputs (default output: ./inventory/intended):

        $ avd-cli generate all -i ./inventory

    Generate with custom output path:

        $ avd-cli generate all -i ./inventory -o ./custom-output

    Generate with specific workflow:

        $ avd-cli generate all -i ./inventory --workflow eos-design

    Using environment variables:

        $ export AVD_CLI_INVENTORY_PATH=./inventory
        $ avd-cli generate all

    Limit to specific groups:

        $ avd-cli generate all -i ./inventory -l spine -l leaf
    """
    verbose = ctx.obj.get("verbose", False)

    # Resolve output path with default if needed
    output_path = resolve_output_path(inventory_path, output_path)

    # Normalize workflow for backward compatibility
    from avd_cli.constants import normalize_workflow

    workflow = normalize_workflow(workflow)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")
        console.print(f"[blue]ℹ[/blue] Workflow: {workflow}")
        if limit_to_groups:
            console.print(f"[blue]ℹ[/blue] Limited to groups: {', '.join(limit_to_groups)}")

    try:
        from avd_cli.logics.generator import generate_all as gen_all
        from avd_cli.logics.loader import InventoryLoader

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        # Validate inventory (skip topology validation for cli-config workflow)
        skip_topology = workflow == "cli-config"
        errors = inventory.validate(skip_topology_validation=skip_topology)
        if errors:
            console.print("[red]✗[/red] Inventory validation failed:")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Generate all outputs
        console.print("[cyan]→[/cyan] Generating configurations, documentation, and tests...")
        limit_groups = list(limit_to_groups) if limit_to_groups else None
        configs, docs, tests = gen_all(inventory, output_path, workflow, limit_groups)

        # Display summary
        console.print("\n[green]✓[/green] Generation complete!")
        from rich.table import Table

        table = Table(title="Generated Files")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta", justify="right")
        table.add_column("Output Path", style="green")

        table.add_row("Configurations", str(len(configs)), str(output_path / "configs"))
        table.add_row("Documentation", str(len(docs)), str(output_path / "documentation"))
        table.add_row("Tests", str(len(tests)), str(output_path / "tests"))

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@generate.command("configs")
@common_generate_options
@click.option(
    "--workflow",
    type=click.Choice(["eos-design", "cli-config", "full", "config-only"], case_sensitive=False),
    default="eos-design",
    envvar="AVD_CLI_WORKFLOW",
    show_envvar=True,
    help=(
        "Workflow type: eos-design (eos_design + eos_cli_config_gen) or cli-config (eos_cli_config_gen only). "
        "Legacy values 'full' and 'config-only' are deprecated."
    ),
)
def generate_configs(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple[str, ...],
    show_deprecation_warnings: bool,
    workflow: str,
) -> None:
    """Generate device configurations only.

    This command generates only device configurations from the AVD inventory,
    skipping documentation and test generation.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Examples
    --------
    Generate configurations (default output: ./inventory/intended):

        $ avd-cli generate configs -i ./inventory

    Generate with custom output path:

        $ avd-cli generate configs -i ./inventory -o ./output

    Generate with cli-config workflow:

        $ avd-cli generate configs -i ./inventory --workflow cli-config

    Using environment variables:

        $ export AVD_CLI_INVENTORY_PATH=./inventory
        $ export AVD_CLI_WORKFLOW=cli-config
        $ avd-cli generate configs
    """
    verbose = ctx.obj.get("verbose", False)

    # Resolve output path with default if needed
    output_path = resolve_output_path(inventory_path, output_path)

    # Normalize workflow for backward compatibility
    from avd_cli.constants import normalize_workflow

    workflow = normalize_workflow(workflow)

    if verbose:
        console.print("[blue]ℹ[/blue] Generating configurations only")
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")

    try:
        from avd_cli.logics.generator import ConfigurationGenerator
        from avd_cli.logics.loader import InventoryLoader

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        # Validate inventory (skip topology validation for cli-config workflow)
        skip_topology = workflow == "cli-config"
        errors = inventory.validate(skip_topology_validation=skip_topology)
        if errors:
            console.print("[red]✗[/red] Inventory validation failed:")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Generate configurations
        console.print("[cyan]→[/cyan] Generating configurations...")
        generator = ConfigurationGenerator(workflow=workflow)
        limit_groups = list(limit_to_groups) if limit_to_groups else None
        configs = generator.generate(inventory, output_path, limit_groups)

        console.print(f"\n[green]✓[/green] Generated {len(configs)} configuration files")
        display_generation_summary("Configurations", len(configs), output_path, "configs")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@generate.command("docs")
@common_generate_options
def generate_docs(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple[str, ...],
    show_deprecation_warnings: bool,
) -> None:
    """Generate documentation only.

    This command generates only documentation from the AVD inventory,
    skipping configuration and test generation.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Examples
    --------
    Generate documentation (default output: ./inventory/intended):

        $ avd-cli generate docs -i ./inventory

    Generate with custom output path:

        $ avd-cli generate docs -i ./inventory -o ./output

    Using environment variables:

        $ export AVD_CLI_INVENTORY_PATH=./inventory
        $ avd-cli generate docs
    """
    verbose = ctx.obj.get("verbose", False)

    # Resolve output path with default if needed
    output_path = resolve_output_path(inventory_path, output_path)

    if verbose:
        console.print("[blue]ℹ[/blue] Generating documentation only")
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")

    try:
        from avd_cli.logics.generator import DocumentationGenerator
        from avd_cli.logics.loader import InventoryLoader

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Generate documentation
        console.print("[cyan]→[/cyan] Generating documentation...")
        generator = DocumentationGenerator()
        limit_groups = list(limit_to_groups) if limit_to_groups else None
        docs = generator.generate(inventory, output_path, limit_groups)

        console.print(f"\n[green]✓[/green] Generated {len(docs)} documentation files")
        display_generation_summary("Documentation", len(docs), output_path, "documentation")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@generate.command("tests")
@common_generate_options
@click.option(
    "--test-type",
    type=click.Choice(["anta", "robot"], case_sensitive=False),
    default="anta",
    envvar="AVD_CLI_TEST_TYPE",
    show_envvar=True,
    help="Type of tests to generate (default: anta)",
)
def generate_tests(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple[str, ...],
    show_deprecation_warnings: bool,
    test_type: str,
) -> None:
    """Generate test files only.

    This command generates only test files (ANTA or Robot Framework) from
    the AVD inventory, skipping configuration and documentation generation.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Examples
    --------
    Generate ANTA tests (default output: ./inventory/intended):

        $ avd-cli generate tests -i ./inventory

    Generate with custom output path:

        $ avd-cli generate tests -i ./inventory -o ./output

    Generate Robot Framework tests:

        $ avd-cli generate tests -i ./inventory --test-type robot

    Using environment variables:

        $ export AVD_CLI_INVENTORY_PATH=./inventory
        $ export AVD_CLI_TEST_TYPE=anta
        $ avd-cli generate tests
    """
    verbose = ctx.obj.get("verbose", False)

    # Resolve output path with default if needed
    output_path = resolve_output_path(inventory_path, output_path)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Generating {test_type.upper()} tests only")
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")

    try:
        from avd_cli.logics.generator import TestGenerator
        from avd_cli.logics.loader import InventoryLoader

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Generate tests
        console.print(f"[cyan]→[/cyan] Generating {test_type.upper()} tests...")
        generator = TestGenerator(test_type=test_type)
        limit_groups = list(limit_to_groups) if limit_to_groups else None
        tests = generator.generate(inventory, output_path, limit_groups)

        console.print(f"\n[green]✓[/green] Generated {len(tests)} test files")
        display_generation_summary("Tests", len(tests), output_path, "tests")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
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


@cli.group()
@click.pass_context
def deploy(ctx: click.Context) -> None:
    """Deploy configurations to network devices.

    This command group provides subcommands for deploying configurations
    to various network device types.

    Examples
    --------
    Deploy configurations to EOS devices:

        $ avd-cli deploy eos -i ./inventory

    Deploy with dry-run mode:

        $ avd-cli deploy eos -i ./inventory --dry-run

    Deploy using merge mode:

        $ avd-cli deploy eos -i ./inventory --merge
    """
    pass


@deploy.command("eos")
@click.option(
    "--inventory-path",
    "-i",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    envvar="AVD_CLI_INVENTORY_PATH",
    show_envvar=True,
    help="Path to Ansible inventory directory",
)
@click.option(
    "--configs-path",
    "-c",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    envvar="AVD_CLI_CONFIGS_PATH",
    show_envvar=True,
    help="Path to configuration files directory (default: <inventory_path>/intended/configs)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    envvar="AVD_CLI_DRY_RUN",
    show_envvar=True,
    help="Validate configurations without applying changes",
)
@click.option(
    "--diff",
    "show_diff",
    is_flag=True,
    default=False,
    envvar="AVD_CLI_SHOW_DIFF",
    show_envvar=True,
    help="Display configuration differences",
)
@click.option(
    "--limit-to-groups",
    "-l",
    multiple=True,
    envvar="AVD_CLI_LIMIT_TO_GROUPS",
    show_envvar=True,
    help="Limit deployment to specific groups (can be used multiple times)",
)
@click.option(
    "--max-concurrent",
    type=int,
    default=10,
    envvar="AVD_CLI_MAX_CONCURRENT",
    show_envvar=True,
    help="Maximum number of concurrent deployments (default: 10)",
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    envvar="AVD_CLI_TIMEOUT",
    show_envvar=True,
    help="Connection timeout in seconds (default: 30)",
)
@click.option(
    "--verify-ssl",
    is_flag=True,
    default=False,
    envvar="AVD_CLI_VERIFY_SSL",
    show_envvar=True,
    help="Verify SSL certificates (default: disabled for lab/dev environments)",
)
@click.pass_context
def deploy_eos(
    ctx: click.Context,
    inventory_path: Path,
    configs_path: Optional[Path],
    dry_run: bool,
    show_diff: bool,
    limit_to_groups: tuple[str, ...],
    max_concurrent: int,
    timeout: int,
    verify_ssl: bool,
) -> None:
    """Deploy configurations to Arista EOS devices via eAPI.

    This command deploys device configurations from the specified directory
    to Arista EOS devices using the eAPI interface. Credentials are extracted
    from the Ansible inventory (ansible_user and ansible_password).

    Configurations are applied using config sessions which provide atomic
    commit/rollback capability and validate syntax before applying changes.

    Note: Config sessions perform MERGE operations (new config is added/updated,
    nothing is removed). True "replace" mode (removing old config) requires
    file-based workflows which are not supported via eAPI.

    By default, SSL certificate verification is disabled to support lab and
    development environments. Use --verify-ssl for production deployments.

    Examples
    --------
    Deploy configurations (with validation):

        $ avd-cli deploy eos -i ./inventory

    Deploy without validation (faster):

        $ avd-cli deploy eos -i ./inventory --no-session

    Dry-run validation:

        $ avd-cli deploy eos -i ./inventory --dry-run --diff

    Deploy to specific groups:

        $ avd-cli deploy eos -i ./inventory -l spine -l leaf

    Deploy with SSL verification:

        $ avd-cli deploy eos -i ./inventory --verify-ssl

    Using environment variables:

        $ export AVD_CLI_INVENTORY_PATH=./inventory
        $ export AVD_CLI_DRY_RUN=true
        $ avd-cli deploy eos
    """
    import asyncio

    verbose = ctx.obj.get("verbose", False)

    # Resolve configs path with default if needed
    if configs_path is None:
        configs_path = inventory_path / "intended" / "configs"
        if verbose:
            console.print(f"[blue]ℹ[/blue] Using default configs path: {configs_path}")

    # Always use config sessions for atomic commit/rollback
    from avd_cli.utils.eapi_client import DeploymentMode
    mode = DeploymentMode.REPLACE

    if verbose:
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Configs path: {configs_path}")
        console.print("[blue]ℹ[/blue] Deployment mode: config sessions (with validation)")
        console.print(f"[blue]ℹ[/blue] Dry run: {dry_run}")
        console.print(f"[blue]ℹ[/blue] Show diff: {show_diff}")
        console.print(f"[blue]ℹ[/blue] SSL verification: {verify_ssl}")

    try:
        from avd_cli.logics.deployer import Deployer

        # Create deployer
        deployer = Deployer(
            inventory_path=inventory_path,
            configs_path=configs_path,
            mode=mode,
            dry_run=dry_run,
            show_diff=show_diff,
            limit_to_groups=list(limit_to_groups) if limit_to_groups else None,
            max_concurrent=max_concurrent,
            timeout=timeout,
            verify_ssl=verify_ssl,
            console=console,
        )

        # Execute deployment
        results = asyncio.run(deployer.deploy())

        # Exit with error code if any deployment failed
        from avd_cli.logics.deployer import DeploymentStatus

        failed_count = sum(1 for r in results if r.status == DeploymentStatus.FAILED)
        if failed_count > 0:
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Deployment error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


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
