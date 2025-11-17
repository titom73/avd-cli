from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import click
from rich.table import Table

from avd_cli.cli.shared import console
from avd_cli.logics.loader import InventoryLoader


@click.command()
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
def info(ctx: click.Context, inventory_path: Path, format: str) -> None:
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        console.print(f"[blue]ℹ[/blue] Reading inventory from: {inventory_path}")
        console.print(f"[blue]ℹ[/blue] Output format: {format}")

    try:
        import json

        if format == "table":
            _print_table(inventory_path)
        elif format == "json":
            info_data = _gather_inventory_data(inventory_path)
            console.print_json(json.dumps(info_data, indent=2))
        elif format == "yaml":
            import yaml as yaml_lib

            info_data = _gather_inventory_data(inventory_path)
            console.print(yaml_lib.dump(info_data, default_flow_style=False))
    except Exception as exc:
        console.print(f"[red]✗[/red] Error: {exc}")
        if verbose:
            console.print_exception()
        raise click.Abort()


def _print_table(inventory_path: Path) -> None:
    loader = InventoryLoader()
    inventory = loader.load(inventory_path)
    total_devices = len(inventory.get_all_devices())
    console.print(f"[green]✓[/green] Loaded {total_devices} devices\n")

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

    if total_devices:
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
        console.print("\n")
        console.print(device_table)


def _gather_inventory_data(inventory_path: Path) -> Dict[str, Any]:
    loader = InventoryLoader()
    inventory = loader.load(inventory_path)
    device_data = []

    for fabric in inventory.fabrics:
        devices = [
            {
                "hostname": device.hostname,
                "type": device.device_type,
                "platform": device.platform,
                "mgmt_ip": str(device.mgmt_ip),
            }
            for device in fabric.get_all_devices()
        ]
        device_data.append(
            {
                "name": fabric.name,
                "design_type": fabric.design_type,
                "spine_devices": len(fabric.spine_devices),
                "leaf_devices": len(fabric.leaf_devices),
                "border_leaf_devices": len(fabric.border_leaf_devices),
                "devices": devices,
            }
        )

    return {
        "total_devices": len(inventory.get_all_devices()),
        "total_fabrics": len(inventory.fabrics),
        "fabrics": device_data,
    }
