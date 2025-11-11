#!/usr/bin/env python
# coding: utf-8 -*-

"""Deployment logic for EOS configuration deployment.

This module provides the core orchestration logic for deploying configurations
to Arista EOS devices using eAPI.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
)
from rich.table import Table

from avd_cli.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    CredentialError,
    DeploymentError,
)
from avd_cli.utils.eapi_client import DeploymentMode, EapiClient, EapiConfig

logger = logging.getLogger(__name__)


def parse_diff_stats(diff_text: Optional[str]) -> tuple[int, int]:
    """Parse diff output and count added/removed lines.

    Parameters
    ----------
    diff_text : Optional[str]
        Diff output text (unified diff format)

    Returns
    -------
    tuple[int, int]
        Tuple of (lines_added, lines_removed)
    """
    if not diff_text:
        return (0, 0)

    lines_added = 0
    lines_removed = 0

    for line in diff_text.split('\n'):
        # Skip metadata lines (--- +++ @@ etc)
        if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
            continue
        # Count additions and removals
        if line.startswith('+'):
            lines_added += 1
        elif line.startswith('-'):
            lines_removed += 1

    return (lines_added, lines_removed)


class DeploymentStatus(Enum):
    """Deployment status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DeviceCredentials:
    """Device credentials extracted from inventory."""

    ansible_user: str
    ansible_password: str


@dataclass
class DeploymentTarget:
    """Deployment target device configuration."""

    hostname: str
    ip_address: str
    credentials: DeviceCredentials
    config_file: Optional[Path] = None
    groups: List[str] = field(default_factory=list)


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""

    hostname: str
    status: DeploymentStatus
    diff: Optional[str] = None
    error: Optional[str] = None
    changes_applied: bool = False
    duration: float = 0.0
    diff_lines_added: int = 0
    diff_lines_removed: int = 0


class Deployer:
    """Orchestrates configuration deployment to EOS devices.

    This class handles:
    - Inventory parsing and credential extraction
    - Configuration file mapping
    - Concurrent deployment to multiple devices
    - Progress tracking and result collection

    Examples
    --------
    >>> deployer = Deployer(
    ...     inventory_path=Path("inventory.yml"),
    ...     configs_path=Path("intended/configs"),
    ...     mode=DeploymentMode.MERGE,
    ...     dry_run=True,
    ... )
    >>> results = await deployer.deploy()
    """

    def __init__(
        self,
        inventory_path: Path,
        configs_path: Optional[Path] = None,
        mode: DeploymentMode = DeploymentMode.REPLACE,
        dry_run: bool = False,
        show_diff: bool = False,
        limit_to_groups: Optional[List[str]] = None,
        max_concurrent: int = 10,
        timeout: int = 30,
        verify_ssl: bool = False,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize deployer.

        Parameters
        ----------
        inventory_path : Path
            Path to Ansible inventory file
        configs_path : Optional[Path]
            Path to configuration files directory. If None, uses inventory_path/intended/configs
        mode : DeploymentMode
            Deployment mode (replace or merge)
        dry_run : bool
            If True, only validate without applying
        show_diff : bool
            If True, display configuration diffs
        limit_to_groups : Optional[List[str]]
            Only deploy to devices in these groups
        max_concurrent : int
            Maximum concurrent deployments
        timeout : int
            Connection timeout in seconds
        verify_ssl : bool
            If True, verify SSL certificates
        console : Optional[Console]
            Rich console for output. If None, creates a new one.
        """
        self.inventory_path = inventory_path
        self.configs_path = configs_path or inventory_path.parent / "intended" / "configs"
        self.mode = mode
        self.dry_run = dry_run
        self.show_diff = show_diff
        self.limit_to_groups = limit_to_groups or []
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.console = console or Console()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self._targets: List[DeploymentTarget] = []
        self._results: List[DeploymentResult] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def _load_inventory(self) -> Dict[str, Any]:
        """Load and parse inventory file.

        Returns
        -------
        Dict[str, Any]
            Parsed inventory data

        Raises
        ------
        DeploymentError
            If inventory file cannot be loaded
        """
        try:
            # Handle both file and directory paths (like generate command)
            inventory_file: Path
            if self.inventory_path.is_file():
                inventory_file = self.inventory_path
            else:
                # Look for inventory.yml or inventory.yaml in directory
                inventory_file = self.inventory_path / "inventory.yml"
                if not inventory_file.exists():
                    inventory_file = self.inventory_path / "inventory.yaml"
                    if not inventory_file.exists():
                        raise DeploymentError(
                            f"No inventory.yml or inventory.yaml found in {self.inventory_path}"
                        )

            with open(inventory_file, encoding='utf-8') as f:
                inventory: Any = yaml.safe_load(f)

            if not inventory:
                raise DeploymentError(f"Empty inventory file: {inventory_file}")

            result: Dict[str, Any] = inventory
            return result

        except FileNotFoundError as e:
            raise DeploymentError(
                f"Inventory file not found: {self.inventory_path}"
            ) from e
        except yaml.YAMLError as e:
            raise DeploymentError(
                f"Invalid YAML in inventory file: {self.inventory_path}: {e}"
            ) from e

    def _extract_credentials(
        self, host_vars: Dict[str, Any], group_vars: Dict[str, Any]
    ) -> DeviceCredentials:
        """Extract credentials from host and group variables.

        Parameters
        ----------
        host_vars : Dict[str, Any]
            Host-specific variables
        group_vars : Dict[str, Any]
            Group-level variables

        Returns
        -------
        DeviceCredentials
            Extracted credentials

        Raises
        ------
        CredentialError
            If required credentials are missing
        """
        # Credentials precedence: host_vars > group_vars
        ansible_user = host_vars.get("ansible_user") or group_vars.get("ansible_user")
        ansible_password = host_vars.get("ansible_password") or group_vars.get(
            "ansible_password"
        )

        if not ansible_user or not ansible_password:
            missing = []
            if not ansible_user:
                missing.append("ansible_user")
            if not ansible_password:
                missing.append("ansible_password")

            raise CredentialError(
                f"Missing required credentials: {', '.join(missing)}. "
                f"Ensure ansible_user and ansible_password are set in inventory."
            )

        return DeviceCredentials(
            ansible_user=ansible_user, ansible_password=ansible_password
        )

    def _extract_hosts_recursive(  # noqa: C901
        self,
        group_data: Dict[str, Any],
        group_name: str,
        parent_vars: Dict[str, Any],
        targets: List[DeploymentTarget],
    ) -> None:
        """Recursively extract hosts from nested group structure.

        Parameters
        ----------
        group_data : Dict[str, Any]
            Group data dictionary
        group_name : str
            Name of the current group
        parent_vars : Dict[str, Any]
            Variables inherited from parent groups
        targets : List[DeploymentTarget]
            List to append discovered targets to
        """
        if not isinstance(group_data, dict):
            return

        # Check if we should process this group based on limit_to_groups filter
        should_process_hosts = True
        if self.limit_to_groups:
            # Only process hosts if current group is in the filter list
            should_process_hosts = group_name in self.limit_to_groups

        # Merge parent vars with current group vars (current takes precedence)
        current_vars = parent_vars.copy()
        if "vars" in group_data:
            current_vars.update(group_data["vars"])

        # Process direct hosts in this group (only if filter allows)
        if should_process_hosts:
            hosts = group_data.get("hosts", {})
            if isinstance(hosts, dict):
                for hostname, host_data in hosts.items():
                    if not isinstance(host_data, dict):
                        continue

                    # Get IP address
                    ansible_host = host_data.get("ansible_host")
                    if not ansible_host:
                        self.logger.warning(
                            "Skipping %s: missing ansible_host in inventory", hostname
                        )
                        continue

                    try:
                        # Extract credentials (host vars override group vars)
                        credentials = self._extract_credentials(host_data, current_vars)

                        # Find config file
                        config_file_path = self.configs_path / f"{hostname}.cfg"
                        config_file: Optional[Path]
                        if not config_file_path.exists():
                            self.logger.warning(
                                "Configuration file not found for %s: %s", hostname, config_file_path
                            )
                            config_file = None
                        else:
                            config_file = config_file_path

                        targets.append(
                            DeploymentTarget(
                                hostname=hostname,
                                ip_address=ansible_host,
                                credentials=credentials,
                                config_file=config_file,
                                groups=[group_name],
                            )
                        )

                    except CredentialError as e:
                        self.logger.error("Skipping %s: %s", hostname, e)
                        continue

        # Recursively process children groups
        children = group_data.get("children", {})
        if isinstance(children, dict):
            for child_name, child_data in children.items():
                self._extract_hosts_recursive(
                    child_data, child_name, current_vars, targets
                )

    def _build_targets(self) -> List[DeploymentTarget]:  # noqa: C901
        """Build list of deployment targets from inventory.

        Returns
        -------
        List[DeploymentTarget]
            List of deployment targets

        Raises
        ------
        DeploymentError
            If inventory structure is invalid
        """
        inventory = self._load_inventory()
        targets: List[DeploymentTarget] = []

        # Parse inventory structure (Ansible YAML format)
        # Support both 'all' group and direct top-level groups
        all_group = inventory.get("all", {})
        children = all_group.get("children", {})

        # If no 'all' group, use top-level groups directly
        if not children:
            children = inventory

        # Process all groups recursively
        for group_name, group_data in children.items():
            # Extract hosts recursively from this group
            # The filtering by limit_to_groups will happen inside the recursive function
            self._extract_hosts_recursive(group_data, group_name, {}, targets)

        if not targets:
            raise DeploymentError(
                "No deployment targets found. Check inventory and group filters."
            )

        return targets

    async def _deploy_to_device(
        self, target: DeploymentTarget, progress: Progress, task_id: TaskID
    ) -> DeploymentResult:
        """Deploy configuration to a single device.

        Parameters
        ----------
        target : DeploymentTarget
            Device target
        progress : Progress
            Rich progress tracker
        task_id : TaskID
            Progress task ID

        Returns
        -------
        DeploymentResult
            Deployment result
        """
        import time

        start_time = time.time()

        # Update progress
        progress.update(
            task_id, description=f"[cyan]{target.hostname}[/cyan] - Connecting..."
        )

        # Check if config file exists
        if not target.config_file or not target.config_file.exists():
            progress.update(
                task_id,
                description=f"[yellow]{target.hostname}[/yellow] - No config file",
            )
            return DeploymentResult(
                hostname=target.hostname,
                status=DeploymentStatus.SKIPPED,
                error="No configuration file found",
                duration=time.time() - start_time,
            )

        try:
            # Acquire semaphore for concurrent control
            async with self._semaphore:
                # Create eAPI client
                eapi_config = EapiConfig(
                    host=target.ip_address,
                    username=target.credentials.ansible_user,
                    password=target.credentials.ansible_password,
                    timeout=self.timeout,
                    verify_ssl=self.verify_ssl,
                )

                async with EapiClient(eapi_config) as client:
                    # Read intended config
                    intended_config = target.config_file.read_text()

                    # Update progress
                    progress.update(
                        task_id,
                        description=f"[cyan]{target.hostname}[/cyan] - Deploying...",
                    )

                    # Apply configuration
                    result = await client.apply_config(
                        intended_config=intended_config,
                        mode=self.mode,
                        dry_run=self.dry_run,
                        show_diff=True,  # Always get diff for statistics
                    )

                    # Parse diff statistics
                    diff_text = result.get("diff")
                    lines_added, lines_removed = parse_diff_stats(diff_text)

                    # Update progress
                    status_text = "Validated" if self.dry_run else "Deployed"
                    progress.update(
                        task_id,
                        description=f"[green]{target.hostname}[/green] - {status_text} ✓",
                    )

                    return DeploymentResult(
                        hostname=target.hostname,
                        status=DeploymentStatus.SUCCESS,
                        diff=diff_text if self.show_diff else None,
                        changes_applied=result.get("changes_applied", False),
                        duration=time.time() - start_time,
                        diff_lines_added=lines_added,
                        diff_lines_removed=lines_removed,
                    )

        except AuthenticationError as e:
            progress.update(
                task_id,
                description=f"[red]{target.hostname}[/red] - Auth failed ✗",
            )
            return DeploymentResult(
                hostname=target.hostname,
                status=DeploymentStatus.FAILED,
                error=f"Authentication failed: {e}",
                duration=time.time() - start_time,
            )

        except ConnectionError as e:
            progress.update(
                task_id,
                description=f"[red]{target.hostname}[/red] - Connection failed ✗",
            )
            return DeploymentResult(
                hostname=target.hostname,
                status=DeploymentStatus.FAILED,
                error=f"Connection failed: {e}",
                duration=time.time() - start_time,
            )

        except ConfigurationError as e:
            progress.update(
                task_id,
                description=f"[red]{target.hostname}[/red] - Config error ✗",
            )
            return DeploymentResult(
                hostname=target.hostname,
                status=DeploymentStatus.FAILED,
                error=f"Configuration error: {e}",
                duration=time.time() - start_time,
            )

        except Exception as e:
            progress.update(
                task_id,
                description=f"[red]{target.hostname}[/red] - Failed ✗",
            )
            return DeploymentResult(
                hostname=target.hostname,
                status=DeploymentStatus.FAILED,
                error=f"Unexpected error: {e}",
                duration=time.time() - start_time,
            )

    async def deploy(self) -> List[DeploymentResult]:
        """Execute deployment to all targets.

        Returns
        -------
        List[DeploymentResult]
            List of deployment results

        Raises
        ------
        DeploymentError
            If deployment cannot proceed
        """
        # Build targets from inventory
        self._targets = self._build_targets()

        # Get credentials from first target for display
        first_target_creds = self._targets[0].credentials if self._targets else None

        self.console.print(
            f"\n[bold cyan]Deployment Plan[/bold cyan] "
            f"({'dry-run' if self.dry_run else 'live deployment'})"
        )
        self.console.print(f"  Mode: [yellow]{self.mode.value}[/yellow]")
        self.console.print(f"  Targets: [cyan]{len(self._targets)}[/cyan] devices")
        self.console.print(
            f"  Concurrency: [cyan]{self.max_concurrent}[/cyan] devices"
        )
        if first_target_creds:
            self.console.print(
                f"  Credentials: [cyan]{first_target_creds.ansible_user}[/cyan] / "
                f"[dim]{'*' * len(first_target_creds.ansible_password)}[/dim]\n"
            )
        else:
            self.console.print()

        # Create a simple spinner for overall progress (no per-device bars)
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            console=self.console,
        ) as progress:
            overall_task = progress.add_task(
                f"Deploying to {len(self._targets)} devices...", total=None
            )

            # Create deployment tasks (no individual progress tracking)
            tasks = []
            for target in self._targets:
                # Create a dummy task just for the method signature
                # We won't update it since we removed per-device bars
                task_id = progress.add_task("", visible=False, total=1)
                tasks.append(
                    self._deploy_to_device(target, progress, task_id)
                )

            # Execute deployments concurrently
            self._results = await asyncio.gather(*tasks, return_exceptions=False)

            # Mark overall progress as complete
            progress.update(overall_task, completed=1)

        # Display results summary
        self._display_results()

        # Display diffs if requested
        if self.show_diff:
            self._display_diffs()

        return self._results

    def _display_results(self) -> None:
        """Display deployment results summary."""
        # Count results by status
        success_count = sum(
            1 for r in self._results if r.status == DeploymentStatus.SUCCESS
        )
        failed_count = sum(
            1 for r in self._results if r.status == DeploymentStatus.FAILED
        )
        skipped_count = sum(
            1 for r in self._results if r.status == DeploymentStatus.SKIPPED
        )

        # Create results table with Diff column
        table = Table(title="\nDeployment Status", show_header=True)
        table.add_column("Hostname", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Duration", justify="right")
        table.add_column("Diff (+/-)", justify="right")
        table.add_column("Error", style="red")

        for result in self._results:
            status_color = {
                DeploymentStatus.SUCCESS: "green",
                DeploymentStatus.FAILED: "red",
                DeploymentStatus.SKIPPED: "yellow",
            }.get(result.status, "white")

            # Format diff statistics with color coding
            diff_display = ""
            if result.status == DeploymentStatus.SUCCESS:
                if result.diff_lines_added > 0 or result.diff_lines_removed > 0:
                    diff_display = (
                        f"[green]+{result.diff_lines_added}[/green] / "
                        f"[red]-{result.diff_lines_removed}[/red]"
                    )
                else:
                    diff_display = "[dim]No changes[/dim]"
            else:
                # For failed or skipped deployments
                diff_display = "[dim]-[/dim]"

            table.add_row(
                result.hostname,
                f"[{status_color}]{result.status.value}[/{status_color}]",
                f"{result.duration:.2f}s",
                diff_display,
                result.error or "",
            )

        self.console.print(table)

        # Summary
        self.console.print("\n[bold]Summary:[/bold]")
        self.console.print(f"  [green]✓[/green] Success: {success_count}")
        self.console.print(f"  [red]✗[/red] Failed: {failed_count}")
        self.console.print(f"  [yellow]○[/yellow] Skipped: {skipped_count}")

        if failed_count > 0:
            self.console.print(
                f"\n[yellow]⚠[/yellow]  {failed_count} deployment{'s' if failed_count > 1 else ''} failed"
            )

    def _display_diffs(self) -> None:
        """Display configuration diffs for all devices."""
        self.console.print("\n[bold cyan]Configuration Diffs[/bold cyan]\n")

        for result in self._results:
            if result.diff and result.status == DeploymentStatus.SUCCESS:
                self.console.print(f"[bold]{result.hostname}:[/bold]")
                self.console.print(result.diff)
                self.console.print()
