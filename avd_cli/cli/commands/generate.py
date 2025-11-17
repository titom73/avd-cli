from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click
from rich.table import Table

from avd_cli.cli.shared import (
    common_generate_options,
    console,
    display_generation_summary,
    resolve_output_path,
    suppress_pyavd_warnings,
)
from avd_cli.constants import normalize_workflow
from avd_cli.logics.loader import InventoryLoader
from avd_cli.utils.device_filter import DeviceFilter


def _merge_patterns(patterns: Tuple[str, ...], legacy_patterns: Tuple[str, ...]) -> List[str]:
    return list(patterns) + list(legacy_patterns)


def _prepare_inventory(
    inventory_path: Path,
    all_patterns: List[str],
    verbose: bool,
    show_deprecation_warnings: bool,
) -> Tuple["Inventory", Optional[DeviceFilter]]:
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
