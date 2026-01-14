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
    limit_patterns: tuple[str, ...],
    limit_to_groups_patterns: tuple[str, ...],
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

    # Merge limit patterns (backward compatibility with --limit-to-groups)
    all_patterns = list(limit_patterns) + list(limit_to_groups_patterns)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")
        console.print(f"[blue]ℹ[/blue] Workflow: {workflow}")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import generate_all as gen_all
        from avd_cli.logics.loader import InventoryLoader
        from avd_cli.utils.device_filter import DeviceFilter

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Create device filter if patterns provided (but don't filter inventory yet)
        device_filter = DeviceFilter.from_patterns(all_patterns)
        if device_filter:
            # Count how many devices match for user feedback
            matching_devices = [
                d for d in inventory.get_all_devices()
                if device_filter.matches_device(d.hostname, d.groups + [d.fabric])
            ]
            if not matching_devices:
                console.print(f"[red]✗[/red] No devices match patterns: {', '.join(all_patterns)}")
                sys.exit(1)
            console.print(f"[blue]ℹ[/blue] Will generate outputs for {len(matching_devices)} filtered devices")

        # Validate inventory (skip topology validation for cli-config workflow)
        # Note: We validate ALL devices to ensure inventory is correct
        skip_topology = workflow == "cli-config"
        errors = inventory.validate(skip_topology_validation=skip_topology)
        if errors:
            console.print("[red]✗[/red] Inventory validation failed:")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)

        # Generate all outputs (pass device_filter to generators)
        console.print("[cyan]→[/cyan] Generating configurations, documentation, and tests...")
        configs, docs, tests = gen_all(inventory, output_path, workflow, device_filter)

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
    limit_patterns: tuple[str, ...],
    limit_to_groups_patterns: tuple[str, ...],
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

    # Merge limit patterns (backward compatibility)
    all_patterns = list(limit_patterns) + list(limit_to_groups_patterns)

    # Resolve output path with default if needed
    output_path = resolve_output_path(inventory_path, output_path)

    # Normalize workflow for backward compatibility
    from avd_cli.constants import normalize_workflow

    workflow = normalize_workflow(workflow)

    if verbose:
        console.print("[blue]ℹ[/blue] Generating configurations only")
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import ConfigurationGenerator
        from avd_cli.logics.loader import InventoryLoader
        from avd_cli.utils.device_filter import DeviceFilter

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Create device filter if patterns provided (but don't filter inventory yet)
        device_filter = DeviceFilter.from_patterns(all_patterns)
        if device_filter:
            # Count how many devices match for user feedback
            matching_devices = [
                d for d in inventory.get_all_devices()
                if device_filter.matches_device(d.hostname, d.groups + [d.fabric])
            ]
            if not matching_devices:
                console.print(f"[red]✗[/red] No devices match patterns: {', '.join(all_patterns)}")
                sys.exit(1)
            console.print(f"[blue]ℹ[/blue] Will generate configs for {len(matching_devices)} filtered devices")

        # Validate inventory (skip topology validation for cli-config workflow)
        # Note: We validate ALL devices to ensure inventory is correct
        skip_topology = workflow == "cli-config"
        errors = inventory.validate(skip_topology_validation=skip_topology)
        if errors:
            console.print("[red]✗[/red] Inventory validation failed:")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)

        # Generate configurations (pass device_filter to generator)
        console.print("[cyan]→[/cyan] Generating configurations...")
        generator = ConfigurationGenerator(workflow=workflow)
        configs = generator.generate(inventory, output_path, device_filter)

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
    limit_patterns: tuple[str, ...],
    limit_to_groups_patterns: tuple[str, ...],
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

    # Merge limit patterns (backward compatibility)
    all_patterns = list(limit_patterns) + list(limit_to_groups_patterns)

    # Resolve output path with default if needed
    output_path = resolve_output_path(inventory_path, output_path)

    if verbose:
        console.print("[blue]ℹ[/blue] Generating documentation only")
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import DocumentationGenerator
        from avd_cli.logics.loader import InventoryLoader
        from avd_cli.utils.device_filter import DeviceFilter

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Create device filter if patterns provided (but don't filter inventory yet)
        device_filter = DeviceFilter.from_patterns(all_patterns)
        if device_filter:
            # Count how many devices match for user feedback
            matching_devices = [
                d for d in inventory.get_all_devices()
                if device_filter.matches_device(d.hostname, d.groups + [d.fabric])
            ]
            if not matching_devices:
                console.print(f"[red]✗[/red] No devices match patterns: {', '.join(all_patterns)}")
                sys.exit(1)
            console.print(f"[blue]ℹ[/blue] Will generate docs for {len(matching_devices)} filtered devices")

        # Generate documentation (pass device_filter to generator)
        console.print("[cyan]→[/cyan] Generating documentation...")
        generator = DocumentationGenerator()
        docs = generator.generate(inventory, output_path, device_filter)

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
    limit_patterns: tuple[str, ...],
    limit_to_groups_patterns: tuple[str, ...],
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

    # Merge limit patterns (backward compatibility)
    all_patterns = list(limit_patterns) + list(limit_to_groups_patterns)

    # Resolve output path with default if needed
    output_path = resolve_output_path(inventory_path, output_path)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Generating {test_type.upper()} tests only")
        console.print(f"[blue]ℹ[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output path: {output_path}")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import TestGenerator
        from avd_cli.logics.loader import InventoryLoader
        from avd_cli.utils.device_filter import DeviceFilter

        # Suppress pyavd deprecation warnings unless explicitly requested
        suppress_pyavd_warnings(show_deprecation_warnings)

        # Load inventory
        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)

        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        # Create device filter if patterns provided (but don't filter inventory yet)
        device_filter = DeviceFilter.from_patterns(all_patterns)
        if device_filter:
            # Count how many devices match for user feedback
            matching_devices = [
                d for d in inventory.get_all_devices()
                if device_filter.matches_device(d.hostname, d.groups + [d.fabric])
            ]
            if not matching_devices:
                console.print(f"[red]✗[/red] No devices match patterns: {', '.join(all_patterns)}")
                sys.exit(1)
            console.print(f"[blue]ℹ[/blue] Will generate tests for {len(matching_devices)} filtered devices")

        # Generate tests (pass device_filter to generator)
        console.print(f"[cyan]→[/cyan] Generating {test_type.upper()} tests...")
        generator = TestGenerator(test_type=test_type)
        tests = generator.generate(inventory, output_path, device_filter)

        console.print(f"\n[green]✓[/green] Generated {len(tests)} test files")
        display_generation_summary("Tests", len(tests), output_path, "tests")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@generate.group()
@click.pass_context
def topology(ctx: click.Context) -> None:
    """Generate topology artifacts from AVD inventory."""
    pass


@topology.command("containerlab")
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
    "--output-path",
    "-o",
    type=click.Path(path_type=Path),
    envvar="AVD_CLI_OUTPUT_PATH",
    show_envvar=True,
    help="Path for output files (default: <inventory>/intended)",
)
@click.option(
    "--limit",
    "-l",
    "limit_patterns",
    multiple=True,
    envvar="AVD_CLI_LIMIT",
    show_envvar=True,
    help="Limit to specific devices (glob patterns, can be specified multiple times)",
)
@click.option(
    "--show-deprecation-warnings",
    is_flag=True,
    envvar="AVD_CLI_SHOW_DEPRECATION_WARNINGS",
    show_envvar=True,
    help="Show pyavd deprecation warnings",
)
@click.option(
    "--startup-dir",
    type=click.Path(path_type=Path, exists=False),
    default="configs",
    show_default=True,
    help="Path to startup configuration files (relative to output path or absolute)",
)
@click.option(
    "--kind",
    default="ceos",
    show_default=True,
    help="Containerlab node kind",
)
@click.option(
    "--image",
    default=None,
    help="Complete Docker image string (e.g., 'ghcr.io/aristanetworks/ceos:4.32.0F'). "
    "Overrides registry/name/version options.",
)
@click.option(
    "--image-registry",
    default="arista",
    show_default=True,
    help="Docker image registry (used when --image not provided)",
)
@click.option(
    "--image-name",
    default="ceos",
    show_default=True,
    help="Docker image name (used when --image not provided)",
)
@click.option(
    "--image-version",
    default="latest",
    show_default=True,
    help="Docker image version/tag (used when --image not provided)",
)
@click.option(
    "--topology-name",
    default="containerlab-topology",
    show_default=True,
    help="Name of the Containerlab topology",
)
@click.pass_context
def generate_topology_containerlab(  # noqa: C901
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_patterns: tuple[str, ...],
    show_deprecation_warnings: bool,
    startup_dir: Path,
    kind: str,
    image: Optional[str],
    image_registry: str,
    image_name: str,
    image_version: str,
    topology_name: str,
) -> None:
    """Generate a Containerlab topology YAML from the AVD inventory.

    This command generates a Containerlab topology definition file from your AVD
    inventory. The topology includes nodes with management IPs, startup configurations,
    and links derived from the ethernet_interfaces configuration.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Examples
    --------
    Generate Containerlab topology:

        $ avd-cli generate topology containerlab -i ./inventory

    With custom output path and node kind:

        $ avd-cli generate topology containerlab -i ./inventory -o ./output --kind ceos

    Filter specific devices:

        $ avd-cli generate topology containerlab -i ./inventory -l spine*
    """
    verbose = ctx.obj.get("verbose", False)
    output_path = resolve_output_path(inventory_path, output_path)

    if verbose:
        console.print("[blue]ℹ[/blue] Generating Containerlab topology")
        if limit_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(limit_patterns)}")

    suppress_pyavd_warnings(show_deprecation_warnings)

    try:
        from avd_cli.logics.loader import InventoryLoader
        from avd_cli.logics.topology import ContainerlabTopologyGenerator
        from avd_cli.utils.device_filter import DeviceFilter

        console.print("[cyan]→[/cyan] Loading inventory...")
        loader = InventoryLoader()
        inventory = loader.load(inventory_path)
        console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

        device_filter = DeviceFilter.from_patterns(list(limit_patterns)) if limit_patterns else None
        if device_filter:
            matching_devices = [
                d for d in inventory.get_all_devices()
                if device_filter.matches_device(d.hostname, d.groups + [d.fabric])
            ]
            if not matching_devices:
                console.print(f"[red]✗[/red] No devices match patterns: {', '.join(limit_patterns)}")
                sys.exit(1)
            console.print(f"[blue]ℹ[/blue] Generating topology for {len(matching_devices)} filtered devices")

        errors = inventory.validate()
        if errors:
            console.print("[red]✗[/red] Inventory validation failed:")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)

        console.print("[cyan]→[/cyan] Generating Containerlab topology...")

        # Derive topology name from inventory path if using default
        generator = ContainerlabTopologyGenerator()
        if topology_name == "containerlab-topology":
            topology_name = generator._derive_topology_name(inventory_path)
            if verbose:
                console.print(f"[blue]ℹ[/blue] Derived topology name: {topology_name}")

        # Construct image string based on priority: --image takes precedence
        node_image = image if image else f"{image_registry}/{image_name}:{image_version}"

        if verbose:
            console.print(f"[blue]ℹ[/blue] Node kind: {kind}")
            console.print(f"[blue]ℹ[/blue] Node image: {node_image}")

        result = generator.generate(
            inventory,
            output_path,
            device_filter=device_filter,
            startup_dir=startup_dir,
            node_kind=kind,
            node_image=node_image,
            topology_name=topology_name,
        )

        console.print(f"\n[green]✓[/green] Topology written to {result.topology_path}")

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


# Register command groups from commands module
cli.add_command(deploy_cmd, name="deploy")
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
