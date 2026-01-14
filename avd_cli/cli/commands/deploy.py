"""Deploy command for AVD CLI.

This module provides the deploy command group and subcommands for deploying
configurations to network devices.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from avd_cli.cli.shared import console


@click.group()
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
)
@click.option(
    "--limit-to-groups",
    "limit_to_groups_patterns",
    multiple=True,
    envvar="AVD_CLI_LIMIT_TO_GROUPS",
    show_envvar=True,
    hidden=True,  # Hide from help but keep for backward compatibility
    help="(Deprecated: use --limit instead) Filter devices by group name pattern",
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
    limit_patterns: tuple[str, ...],
    limit_to_groups_patterns: tuple[str, ...],
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
    verbose = ctx.obj.get("verbose", False)

    # Merge limit patterns (backward compatibility)
    all_patterns = list(limit_patterns) + list(limit_to_groups_patterns)

    # Resolve configs path with default if needed
    if configs_path is None:
        configs_path = inventory_path / "intended" / "configs"
        if verbose:
            console.print(f"[blue]ℹ[/blue] Using default configs path: {configs_path}")

    # Always use config sessions for atomic commit/rollback
    from avd_cli.utils.eapi_client import DeploymentMode

    mode = DeploymentMode.REPLACE

    if verbose:
        console.print(f"[blue]\u2139[/blue] Inventory path: {inventory_path}")
        console.print(f"[blue]\u2139[/blue] Configs path: {configs_path}")
        console.print("[blue]\u2139[/blue] Deployment mode: config sessions (with validation)")
        console.print(f"[blue]\u2139[/blue] Dry run: {dry_run}")
        console.print(f"[blue]\u2139[/blue] Show diff: {show_diff}")
        console.print(f"[blue]\u2139[/blue] SSL verification: {verify_ssl}")
        if all_patterns:
            console.print(f"[blue]\u2139[/blue] Filter patterns: {', '.join(all_patterns)}")

    try:
        from avd_cli.logics.deployer import Deployer
        from avd_cli.utils.device_filter import DeviceFilter

        # Create device filter from patterns (supports hostname and group filtering)
        device_filter = DeviceFilter.from_patterns(all_patterns) if all_patterns else None

        # Create deployer with device filter
        deployer = Deployer(
            inventory_path=inventory_path,
            configs_path=configs_path,
            mode=mode,
            dry_run=dry_run,
            show_diff=show_diff,
            device_filter=device_filter,
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
        console.print(f"[red]\u2717[/red] Deployment error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)
