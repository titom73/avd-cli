#!/usr/bin/env python
# coding: utf-8 -*-

"""CLI commands for managing pyavd package version."""

import click

from avd_cli.cli.shared import console
from avd_cli.utils.package_manager import PackageManager, PackageManagerType
from avd_cli.utils.version import get_pyavd_version


@click.group()
def pyavd_cmd() -> None:
    """Manage pyavd package version.

    This command group provides utilities to manage the pyavd dependency,
    including installing specific versions.

    Examples
    --------
    Show current pyavd version:

        $ avd-cli pyavd version

    Install a specific pyavd version:

        $ avd-cli pyavd install 5.7.0

    Install using pip explicitly:

        $ avd-cli pyavd install 5.7.0 --package-manager pip

    Preview install command without executing:

        $ avd-cli pyavd install 5.7.0 --dry-run
    """


@pyavd_cmd.command("version")
def version() -> None:
    """Display the currently installed pyavd version."""
    pyavd_ver = get_pyavd_version()
    console.print(f"pyavd version: [cyan]{pyavd_ver}[/cyan]")


@pyavd_cmd.command("install")
@click.argument("version")
@click.option(
    "--package-manager",
    "-m",
    type=click.Choice(["auto", "pip", "uv"], case_sensitive=False),
    default="auto",
    help="Package manager to use for installation (default: auto-detect).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show the command that would be executed without running it.",
)
@click.pass_context
def install(ctx: click.Context, version: str, package_manager: str, dry_run: bool) -> None:
    """Install a specific version of pyavd.

    VERSION is the pyavd version to install (e.g., 5.7.0, 5.6.0).

    This command supports both upgrade and downgrade operations. The user
    is responsible for selecting a version compatible with their Python version.

    Note: pyavd 5.x requires Python >= 3.10.
    """
    verbose = ctx.obj.get("verbose", False) if ctx.obj else False

    manager_type = PackageManagerType(package_manager)

    try:
        pm = PackageManager(manager=manager_type)

        if verbose:
            console.print(f"[blue]ℹ[/blue] Using package manager: {pm.manager}")

        if dry_run:
            result = pm.install_package("pyavd", version, dry_run=True)
            console.print("[yellow]Dry run mode[/yellow] - command that would be executed:")
            console.print(f"  [dim]{' '.join(result.command)}[/dim]")
            return

        console.print(f"[blue]ℹ[/blue] Installing pyavd=={version} using {pm.manager}...")

        result = pm.install_package("pyavd", version)

        if result.success:
            console.print(f"[green]✓[/green] Successfully installed pyavd=={version}")
            new_version = get_pyavd_version()
            console.print(f"[blue]ℹ[/blue] Current pyavd version: {new_version}")
        else:
            console.print(f"[red]✗[/red] Failed to install pyavd=={version}")
            if result.error_message:
                console.print(f"[red]Error:[/red] {result.error_message}")
            raise click.Abort()

    except RuntimeError as exc:
        console.print(f"[red]✗[/red] {exc}")
        raise click.Abort()
