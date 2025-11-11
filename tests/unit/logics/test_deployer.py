#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for deployment orchestrator."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from avd_cli.exceptions import CredentialError, DeploymentError
from avd_cli.logics.deployer import (
    Deployer,
    DeploymentResult,
    DeploymentStatus,
    DeploymentTarget,
    DeviceCredentials,
    parse_diff_stats,
)
from avd_cli.utils.eapi_client import DeploymentMode


class TestParseDiffStats:
    """Test parse_diff_stats function."""

    def test_parse_unified_diff(self) -> None:
        """Test parsing of unified diff output."""
        diff_text = """--- running-config
+++ intended-config
@@ -1,5 +1,7 @@
 hostname spine-1
 !
+interface Ethernet1
+   description uplink
 !
-interface Loopback0
-   ip address 10.0.0.1/32
+interface Loopback0
+   ip address 10.0.0.2/32
"""
        added, removed = parse_diff_stats(diff_text)
        assert added == 4  # +interface Ethernet1, +description, +interface Loopback0, +ip address
        assert removed == 2  # -interface Loopback0, -ip address

    def test_parse_empty_diff(self) -> None:
        """Test parsing of empty diff."""
        added, removed = parse_diff_stats(None)
        assert added == 0
        assert removed == 0

        added, removed = parse_diff_stats("")
        assert added == 0
        assert removed == 0

    def test_parse_additions_only(self) -> None:
        """Test parsing diff with only additions."""
        diff_text = """--- running-config
+++ intended-config
@@ -1,3 +1,5 @@
 hostname spine-1
+interface Ethernet1
+   description new
"""
        added, removed = parse_diff_stats(diff_text)
        assert added == 2
        assert removed == 0

    def test_parse_removals_only(self) -> None:
        """Test parsing diff with only removals."""
        diff_text = """--- running-config
+++ intended-config
@@ -1,5 +1,3 @@
 hostname spine-1
-interface Ethernet1
-   description old
"""
        added, removed = parse_diff_stats(diff_text)
        assert added == 0
        assert removed == 2


class TestDeviceCredentials:
    """Test DeviceCredentials dataclass."""

    def test_credentials_creation(self) -> None:
        """Test credentials creation."""
        creds = DeviceCredentials(
            ansible_user="admin", ansible_password="admin123"
        )

        assert creds.ansible_user == "admin"
        assert creds.ansible_password == "admin123"


class TestDeploymentTarget:
    """Test DeploymentTarget dataclass."""

    def test_target_creation(self) -> None:
        """Test deployment target creation."""
        creds = DeviceCredentials(ansible_user="admin", ansible_password="admin123")
        target = DeploymentTarget(
            hostname="spine-1",
            ip_address="192.168.0.10",
            credentials=creds,
            config_file=Path("/configs/spine-1.cfg"),
            groups=["spines"],
        )

        assert target.hostname == "spine-1"
        assert target.ip_address == "192.168.0.10"
        assert target.credentials == creds
        assert target.config_file == Path("/configs/spine-1.cfg")
        assert target.groups == ["spines"]

    def test_target_without_config(self) -> None:
        """Test deployment target without config file."""
        creds = DeviceCredentials(ansible_user="admin", ansible_password="admin123")
        target = DeploymentTarget(
            hostname="spine-1",
            ip_address="192.168.0.10",
            credentials=creds,
        )

        assert target.config_file is None
        assert target.groups == []


class TestDeploymentResult:
    """Test DeploymentResult dataclass."""

    def test_successful_result(self) -> None:
        """Test successful deployment result."""
        result = DeploymentResult(
            hostname="spine-1",
            status=DeploymentStatus.SUCCESS,
            diff="config diff",
            changes_applied=True,
            duration=2.5,
        )

        assert result.hostname == "spine-1"
        assert result.status == DeploymentStatus.SUCCESS
        assert result.diff == "config diff"
        assert result.changes_applied is True
        assert result.duration == 2.5
        assert result.error is None

    def test_failed_result(self) -> None:
        """Test failed deployment result."""
        result = DeploymentResult(
            hostname="spine-1",
            status=DeploymentStatus.FAILED,
            error="Connection timeout",
            duration=30.0,
        )

        assert result.hostname == "spine-1"
        assert result.status == DeploymentStatus.FAILED
        assert result.error == "Connection timeout"
        assert result.changes_applied is False
        assert result.diff is None


@pytest.fixture
def sample_inventory(tmp_path: Path) -> Path:
    """Create sample inventory file."""
    inventory_data = {
        "all": {
            "children": {
                "spines": {
                    "vars": {
                        "ansible_user": "admin",
                        "ansible_password": "admin123",
                    },
                    "hosts": {
                        "spine-1": {"ansible_host": "192.168.0.10"},
                        "spine-2": {"ansible_host": "192.168.0.11"},
                    },
                },
                "leafs": {
                    "vars": {
                        "ansible_user": "netadmin",
                    },
                    "hosts": {
                        "leaf-1": {
                            "ansible_host": "192.168.0.20",
                            "ansible_password": "leaf123",
                        },
                        "leaf-2": {
                            "ansible_host": "192.168.0.21",
                            "ansible_password": "leaf123",
                        },
                    },
                },
            }
        }
    }

    inventory_file = tmp_path / "inventory.yml"
    with open(inventory_file, "w", encoding='utf-8') as f:
        yaml.dump(inventory_data, f)

    return inventory_file


@pytest.fixture
def sample_configs(tmp_path: Path) -> Path:
    """Create sample configuration files."""
    configs_dir = tmp_path / "intended" / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)

    # Create config files
    for device in ["spine-1", "spine-2", "leaf-1", "leaf-2"]:
        config_file = configs_dir / f"{device}.cfg"
        config_file.write_text(f"hostname {device}\ninterface Ethernet1\n   description test\n")

    return configs_dir


class TestDeployer:
    """Test Deployer class."""

    def test_deployer_initialization(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test deployer initialization."""
        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            mode=DeploymentMode.REPLACE,
            dry_run=True,
            show_diff=True,
            limit_to_groups=["spines"],
            max_concurrent=5,
            timeout=60,
            verify_ssl=True,
        )

        assert deployer.inventory_path == sample_inventory
        assert deployer.configs_path == sample_configs
        assert deployer.mode == DeploymentMode.REPLACE
        assert deployer.dry_run is True
        assert deployer.show_diff is True
        assert deployer.limit_to_groups == ["spines"]
        assert deployer.max_concurrent == 5
        assert deployer.timeout == 60
        assert deployer.verify_ssl is True

    def test_deployer_default_configs_path(self, sample_inventory: Path) -> None:
        """Test deployer with default configs path."""
        deployer = Deployer(inventory_path=sample_inventory)

        expected_path = sample_inventory.parent / "intended" / "configs"
        assert deployer.configs_path == expected_path

    def test_load_inventory_success(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test successful inventory loading."""
        deployer = Deployer(
            inventory_path=sample_inventory, configs_path=sample_configs
        )

        inventory = deployer._load_inventory()

        assert "all" in inventory
        assert "children" in inventory["all"]
        assert "spines" in inventory["all"]["children"]
        assert "leafs" in inventory["all"]["children"]

    def test_load_inventory_not_found(self, tmp_path: Path) -> None:
        """Test inventory loading with missing file."""
        nonexistent = tmp_path / "nonexistent.yml"
        deployer = Deployer(inventory_path=nonexistent)

        with pytest.raises(DeploymentError, match="No inventory.yml or inventory.yaml found"):
            deployer._load_inventory()

    def test_load_inventory_invalid_yaml(self, tmp_path: Path) -> None:
        """Test inventory loading with invalid YAML."""
        invalid_file = tmp_path / "invalid.yml"
        invalid_file.write_text("invalid: yaml: content:")

        deployer = Deployer(inventory_path=invalid_file)

        with pytest.raises(DeploymentError, match="Invalid YAML"):
            deployer._load_inventory()

    def test_load_inventory_from_directory(self, tmp_path: Path) -> None:
        """Test inventory loading from directory (inventory.yml)."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        inventory_data = {
            "all": {
                "children": {
                    "spines": {
                        "hosts": {"spine1": {"ansible_host": "10.0.0.1"}}
                    }
                }
            }
        }

        inventory_file = inventory_dir / "inventory.yml"
        with open(inventory_file, "w", encoding='utf-8') as f:
            yaml.dump(inventory_data, f)

        deployer = Deployer(inventory_path=inventory_dir)
        inventory = deployer._load_inventory()

        assert "all" in inventory
        assert "children" in inventory["all"]

    def test_load_inventory_from_directory_yaml_extension(
        self, tmp_path: Path
    ) -> None:
        """Test inventory loading from directory (inventory.yaml)."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        inventory_data = {
            "all": {
                "children": {
                    "spines": {
                        "hosts": {"spine1": {"ansible_host": "10.0.0.1"}}
                    }
                }
            }
        }

        # Use .yaml extension instead of .yml
        inventory_file = inventory_dir / "inventory.yaml"
        with open(inventory_file, "w", encoding='utf-8') as f:
            yaml.dump(inventory_data, f)

        deployer = Deployer(inventory_path=inventory_dir)
        inventory = deployer._load_inventory()

        assert "all" in inventory

    def test_load_inventory_from_directory_not_found(
        self, tmp_path: Path
    ) -> None:
        """Test inventory loading from directory with no inventory file."""
        inventory_dir = tmp_path / "empty_inventory"
        inventory_dir.mkdir()

        deployer = Deployer(inventory_path=inventory_dir)

        with pytest.raises(
            DeploymentError, match="No inventory.yml or inventory.yaml found"
        ):
            deployer._load_inventory()

    def test_extract_credentials_from_host_vars(self) -> None:
        """Test credential extraction from host variables."""
        deployer = Deployer(inventory_path=Path("dummy"))

        host_vars = {"ansible_user": "hostuser", "ansible_password": "hostpass"}
        group_vars = {"ansible_user": "groupuser", "ansible_password": "grouppass"}

        creds = deployer._extract_credentials(host_vars, group_vars)

        # Host vars take precedence
        assert creds.ansible_user == "hostuser"
        assert creds.ansible_password == "hostpass"

    def test_extract_credentials_from_group_vars(self) -> None:
        """Test credential extraction from group variables."""
        deployer = Deployer(inventory_path=Path("dummy"))

        host_vars: Dict[str, Any] = {}
        group_vars = {"ansible_user": "groupuser", "ansible_password": "grouppass"}

        creds = deployer._extract_credentials(host_vars, group_vars)

        assert creds.ansible_user == "groupuser"
        assert creds.ansible_password == "grouppass"

    def test_extract_credentials_missing_user(self) -> None:
        """Test credential extraction with missing username."""
        deployer = Deployer(inventory_path=Path("dummy"))

        host_vars = {"ansible_password": "pass"}
        group_vars: Dict[str, Any] = {}

        with pytest.raises(CredentialError, match="ansible_user"):
            deployer._extract_credentials(host_vars, group_vars)

    def test_extract_credentials_missing_password(self) -> None:
        """Test credential extraction with missing password."""
        deployer = Deployer(inventory_path=Path("dummy"))

        host_vars = {"ansible_user": "user"}
        group_vars: Dict[str, Any] = {}

        with pytest.raises(CredentialError, match="ansible_password"):
            deployer._extract_credentials(host_vars, group_vars)

    def test_build_targets_all_groups(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test building targets from all groups."""
        deployer = Deployer(
            inventory_path=sample_inventory, configs_path=sample_configs
        )

        targets = deployer._build_targets()

        assert len(targets) == 4
        hostnames = {t.hostname for t in targets}
        assert hostnames == {"spine-1", "spine-2", "leaf-1", "leaf-2"}

    def test_build_targets_limited_groups(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test building targets with group filtering."""
        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            limit_to_groups=["spines"],
        )

        targets = deployer._build_targets()

        assert len(targets) == 2
        hostnames = {t.hostname for t in targets}
        assert hostnames == {"spine-1", "spine-2"}

    def test_build_targets_missing_config_files(
        self, sample_inventory: Path, tmp_path: Path
    ) -> None:
        """Test building targets with missing config files."""
        empty_configs = tmp_path / "empty_configs"
        empty_configs.mkdir()

        deployer = Deployer(
            inventory_path=sample_inventory, configs_path=empty_configs
        )

        targets = deployer._build_targets()

        # Targets are created but config_file is None
        assert len(targets) == 4
        assert all(t.config_file is None or not t.config_file.exists() for t in targets)

    @pytest.mark.asyncio
    async def test_deploy_to_device_success(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test successful device deployment."""
        from rich.progress import Progress

        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            dry_run=True,
        )

        creds = DeviceCredentials(ansible_user="admin", ansible_password="admin123")
        target = DeploymentTarget(
            hostname="spine-1",
            ip_address="192.168.0.10",
            credentials=creds,
            config_file=sample_configs / "spine-1.cfg",
        )

        with Progress() as progress:
            task_id = progress.add_task("test", total=1)

            with patch(
                "avd_cli.logics.deployer.EapiClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                diff_content = (
                    "--- running-config\n+++ intended-config\n"
                    "@@ -1,3 +1,5 @@\n hostname spine-1\n"
                    "+interface Ethernet1\n+   description test\n"
                    "-interface Loopback0"
                )
                mock_client.apply_config.return_value = {
                    "success": True,
                    "diff": diff_content,
                    "changes_applied": False,
                }
                mock_client_class.return_value = mock_client

                result = await deployer._deploy_to_device(target, progress, task_id)

                assert result.status == DeploymentStatus.SUCCESS
                assert result.hostname == "spine-1"
                assert result.diff is None  # Not shown when show_diff=False
                assert result.changes_applied is False
                assert result.diff_lines_added == 2  # +interface Ethernet1, +description
                assert result.diff_lines_removed == 1  # -interface Loopback0

    @pytest.mark.asyncio
    async def test_deploy_to_device_missing_config(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test deployment with missing config file."""
        from rich.progress import Progress

        deployer = Deployer(
            inventory_path=sample_inventory, configs_path=sample_configs
        )

        creds = DeviceCredentials(ansible_user="admin", ansible_password="admin123")
        target = DeploymentTarget(
            hostname="missing-device",
            ip_address="192.168.0.99",
            credentials=creds,
            config_file=None,
        )

        with Progress() as progress:
            task_id = progress.add_task("test", total=1)

            result = await deployer._deploy_to_device(target, progress, task_id)

            assert result.status == DeploymentStatus.SKIPPED
            assert result.hostname == "missing-device"
            assert result.error is not None
            assert "No configuration file" in result.error
            assert result.diff_lines_added == 0
            assert result.diff_lines_removed == 0

    @pytest.mark.asyncio
    async def test_deploy_all_devices(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test deployment to all devices."""
        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            dry_run=True,
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": "--- running-config\n+++ intended-config\n+new line\n-old line",
                "changes_applied": False,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            assert len(results) == 4
            assert all(r.status == DeploymentStatus.SUCCESS for r in results)
            # Verify diff stats are populated
            assert all(r.diff_lines_added == 1 for r in results)
            assert all(r.diff_lines_removed == 1 for r in results)

    @pytest.mark.asyncio
    async def test_deploy_with_group_limit(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test deployment with group filtering."""
        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            limit_to_groups=["leafs"],
            dry_run=True,
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": "+added line",
                "changes_applied": False,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # Only leaf devices should be deployed
            assert len(results) == 2
            hostnames = {r.hostname for r in results}
            assert hostnames == {"leaf-1", "leaf-2"}
            # Verify diff stats
            assert all(r.diff_lines_added == 1 for r in results)
            assert all(r.diff_lines_removed == 0 for r in results)

    def test_display_results_with_diff_stats(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test that _display_results shows diff statistics."""
        from io import StringIO
        from rich.console import Console

        # Create a console that captures output
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True)

        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            console=console,
        )

        # Create mock results with diff stats
        deployer._results = [
            DeploymentResult(
                hostname="spine-1",
                status=DeploymentStatus.SUCCESS,
                diff_lines_added=15,
                diff_lines_removed=3,
                duration=2.5,
            ),
            DeploymentResult(
                hostname="spine-2",
                status=DeploymentStatus.SUCCESS,
                diff_lines_added=0,
                diff_lines_removed=0,
                duration=1.2,
            ),
            DeploymentResult(
                hostname="leaf-1",
                status=DeploymentStatus.FAILED,
                error="Connection timeout",
                duration=30.0,
            ),
        ]

        deployer._display_results()

        output = output_buffer.getvalue()

        # Verify table title
        assert "Deployment Status" in output

        # Verify column headers
        assert "Hostname" in output
        assert "Status" in output
        assert "Duration" in output
        assert "Diff (+/-)" in output

        # Verify data rows (hostnames)
        assert "spine-1" in output
        assert "spine-2" in output
        assert "leaf-1" in output

        # Verify diff stats appear (the exact format might vary with Rich rendering)
        assert "15" in output  # Added lines for spine-1
        assert "3" in output   # Removed lines for spine-1

    def test_display_results_no_changes(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test display when there are no changes."""
        from io import StringIO
        from rich.console import Console

        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=True)

        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            console=console,
        )

        deployer._results = [
            DeploymentResult(
                hostname="device-1",
                status=DeploymentStatus.SUCCESS,
                diff_lines_added=0,
                diff_lines_removed=0,
                duration=1.0,
            ),
        ]

        deployer._display_results()

        output = output_buffer.getvalue()

        # Should show "No changes" for devices with 0/0 diff
        assert "No changes" in output or "0" in output

    @pytest.mark.asyncio
    async def test_show_diff_stores_full_diff(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test that show_diff=True stores the full diff text."""
        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            show_diff=True,  # Enable diff storage
            dry_run=True,
        )

        diff_text = "--- running\n+++ intended\n+new line\n-old line"

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": diff_text,
                "changes_applied": False,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # Verify diff is stored when show_diff=True
            assert all(r.diff == diff_text for r in results)
            assert all(r.diff_lines_added == 1 for r in results)
            assert all(r.diff_lines_removed == 1 for r in results)

    @pytest.mark.asyncio
    async def test_show_diff_false_no_storage(
        self, sample_inventory: Path, sample_configs: Path
    ) -> None:
        """Test that show_diff=False does not store the full diff."""
        deployer = Deployer(
            inventory_path=sample_inventory,
            configs_path=sample_configs,
            show_diff=False,  # Disable diff storage
            dry_run=True,
        )

        diff_text = "--- running\n+++ intended\n+new line\n-old line"

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": diff_text,
                "changes_applied": False,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # Verify diff is NOT stored when show_diff=False, but stats are
            assert all(r.diff is None for r in results)
            assert all(r.diff_lines_added == 1 for r in results)
            assert all(r.diff_lines_removed == 1 for r in results)
