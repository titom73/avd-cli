from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

import click
from rich.table import Table

if TYPE_CHECKING:
    from avd_cli.models.inventory import InventoryData

# pylint: disable=wrong-import-position  # Imports after TYPE_CHECKING block
from avd_cli.cli.shared import (
    common_generate_options,
    console,
    display_generation_summary,
    resolve_output_path,
    suppress_pyavd_warnings,
)
from avd_cli.constants import normalize_workflow
from avd_cli.logics.loader import InventoryLoader
from avd_cli.logics.topology import ContainerlabTopologyGenerator
from avd_cli.utils.device_filter import DeviceFilter


def _merge_patterns(patterns: Tuple[str, ...], legacy_patterns: Tuple[str, ...]) -> List[str]:
    return list(patterns) + list(legacy_patterns)


def _prepare_inventory(
    inventory_path: Path,
    all_patterns: List[str],
    verbose: bool,
    show_deprecation_warnings: bool,
) -> Tuple["InventoryData", Optional[DeviceFilter]]:
    suppress_pyavd_warnings(show_deprecation_warnings)

    loader = InventoryLoader()
    inventory = loader.load(inventory_path)
    console.print(f"[green]✓[/green] Loaded {len(inventory.get_all_devices())} devices")

    device_filter = DeviceFilter.from_patterns(all_patterns) if all_patterns else None
    if device_filter:
        matching_devices = [
            d
            for d in inventory.get_all_devices()
            if device_filter.matches_device(d.hostname, d.groups + [d.fabric])
        ]
        if not matching_devices:
            console.print(f"[red]✗[/red] No devices match patterns: {', '.join(all_patterns)}")
            sys.exit(1)
        if verbose:
            console.print(f"[blue]ℹ[/blue] Filter will apply to {len(matching_devices)} devices")
    return inventory, device_filter


@click.group(name="generate")
@click.pass_context
def generate(ctx: click.Context) -> None:
    """Generate configurations, documentation, and tests from AVD inventory."""
    pass


@generate.command("all")
@common_generate_options
@click.option(
    "--workflow",
    type=click.Choice(["eos-design", "cli-config", "full", "config-only"], case_sensitive=False),
    default="eos-design",
    envvar="AVD_CLI_WORKFLOW",
    show_envvar=True,
)
def generate_all(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Path,
    limit_patterns: Tuple[str, ...],
    limit_to_groups_patterns: Tuple[str, ...],
    show_deprecation_warnings: bool,
    workflow: str,
) -> None:
    verbose = ctx.obj.get("verbose", False)
    all_patterns = _merge_patterns(limit_patterns, limit_to_groups_patterns)
    output_path = resolve_output_path(inventory_path, output_path)
    workflow = normalize_workflow(workflow)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Workflow: {workflow}")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import generate_all as gen_all

        inventory, device_filter = _prepare_inventory(
            inventory_path, all_patterns, verbose, show_deprecation_warnings
        )
        skip_topology = workflow == "cli-config"
        errors = inventory.validate(skip_topology_validation=skip_topology)
        if errors:
            console.print("[red]✗[/red] Inventory validation failed:")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)

        console.print("[cyan]→[/cyan] Generating configurations, documentation, and tests...")
        configs, docs, tests = gen_all(inventory, output_path, workflow, device_filter)

        console.print("\n[green]✓[/green] Generation complete!")
        table = Table(title="Generated Files")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta", justify="right")
        table.add_column("Output Path", style="green")
        table.add_row("Configurations", str(len(configs)), str(output_path / "configs"))
        table.add_row("Documentation", str(len(docs)), str(output_path / "documentation"))
        table.add_row("Tests", str(len(tests)), str(output_path / "tests"))
        console.print(table)

    except Exception as exc:
        console.print(f"[red]✗[/red] Error: {exc}")
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
)
def generate_configs(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Path,
    limit_patterns: Tuple[str, ...],
    limit_to_groups_patterns: Tuple[str, ...],
    show_deprecation_warnings: bool,
    workflow: str,
) -> None:
    verbose = ctx.obj.get("verbose", False)
    all_patterns = _merge_patterns(limit_patterns, limit_to_groups_patterns)
    output_path = resolve_output_path(inventory_path, output_path)
    workflow = normalize_workflow(workflow)

    if verbose:
        console.print("[blue]ℹ[/blue] Generating configurations only")
        console.print(f"[blue]ℹ[/blue] Workflow: {workflow}")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import ConfigurationGenerator

        inventory, device_filter = _prepare_inventory(
            inventory_path, all_patterns, verbose, show_deprecation_warnings
        )
        skip_topology = workflow == "cli-config"
        errors = inventory.validate(skip_topology_validation=skip_topology)
        if errors:
            console.print("[red]✗[/red] Inventory validation failed:")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            sys.exit(1)

        console.print("[cyan]→[/cyan] Generating configurations...")
        generator = ConfigurationGenerator(workflow=workflow)
        configs = generator.generate(inventory, output_path, device_filter)

        console.print(f"\n[green]✓[/green] Generated {len(configs)} configuration files")
        display_generation_summary("Configurations", len(configs), output_path, "configs")

    except Exception as exc:
        console.print(f"[red]✗[/red] Error: {exc}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@generate.command("docs")
@common_generate_options
def generate_docs(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Path,
    limit_patterns: Tuple[str, ...],
    limit_to_groups_patterns: Tuple[str, ...],
    show_deprecation_warnings: bool,
) -> None:
    verbose = ctx.obj.get("verbose", False)
    all_patterns = _merge_patterns(limit_patterns, limit_to_groups_patterns)
    output_path = resolve_output_path(inventory_path, output_path)

    if verbose:
        console.print("[blue]ℹ[/blue] Generating documentation only")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import DocumentationGenerator

        inventory, device_filter = _prepare_inventory(
            inventory_path, all_patterns, verbose, show_deprecation_warnings
        )

        console.print("[cyan]→[/cyan] Generating documentation...")
        generator = DocumentationGenerator()
        docs = generator.generate(inventory, output_path, device_filter)

        console.print(f"\n[green]✓[/green] Generated {len(docs)} documentation files")
        display_generation_summary("Documentation", len(docs), output_path, "documentation")

    except Exception as exc:
        console.print(f"[red]✗[/red] Error: {exc}")
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
)
def generate_tests(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Path,
    limit_patterns: Tuple[str, ...],
    limit_to_groups_patterns: Tuple[str, ...],
    show_deprecation_warnings: bool,
    test_type: str,
) -> None:
    verbose = ctx.obj.get("verbose", False)
    all_patterns = _merge_patterns(limit_patterns, limit_to_groups_patterns)
    output_path = resolve_output_path(inventory_path, output_path)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Generating {test_type.upper()} tests only")
        if all_patterns:
            console.print(f"[blue]ℹ[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.generator import TestGenerator

        inventory, device_filter = _prepare_inventory(
            inventory_path, all_patterns, verbose, show_deprecation_warnings
        )

        console.print(f"[cyan]→[/cyan] Generating {test_type.upper()} tests...")
        generator = TestGenerator(test_type=test_type)
        tests = generator.generate(inventory, output_path, device_filter)

        console.print(f"\n[green]✓[/green] Generated {len(tests)} test files")
        display_generation_summary("Tests", len(tests), output_path, "tests")

    except Exception as exc:
        console.print(f"[red]✗[/red] Error: {exc}")
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
    limit_patterns: Tuple[str, ...],
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
