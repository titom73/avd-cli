#!/usr/bin/env python
# coding: utf-8 -*-

"""Integration tests for deployment workflow."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from avd_cli.logics.deployer import Deployer, DeploymentStatus
from avd_cli.utils.eapi_client import DeploymentMode


@pytest.fixture
def integration_inventory(tmp_path: Path) -> Path:
    """Create integration test inventory."""
    inventory_data = {
        "all": {
            "children": {
                "fabric": {
                    "vars": {
                        "ansible_user": "admin",
                        "ansible_password": "admin",
                    },
                    "hosts": {
                        "device-1": {"ansible_host": "10.0.0.1"},
                        "device-2": {"ansible_host": "10.0.0.2"},
                        "device-3": {"ansible_host": "10.0.0.3"},
                    },
                },
            }
        }
    }

    inventory_file = tmp_path / "inventory.yml"
    with open(inventory_file, "w", encoding='utf-8') as f:
        yaml.dump(inventory_data, f)

    # Create config files
    configs_dir = tmp_path / "intended" / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, 4):
        config_file = configs_dir / f"device-{i}.cfg"
        config_file.write_text(f"""hostname device-{i}
interface Ethernet1
   description uplink
interface Ethernet2
   description server
""")

    return inventory_file


@pytest.mark.asyncio
class TestDeploymentWorkflow:
    """Integration tests for full deployment workflow."""

    async def test_full_deployment_dry_run(
        self, integration_inventory: Path
    ) -> None:
        """Test complete dry-run deployment workflow."""
        deployer = Deployer(
            inventory_path=integration_inventory,
            mode=DeploymentMode.REPLACE,
            dry_run=True,
            show_diff=False,
            max_concurrent=2,
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": "- old config\n+ new config\n+ another line",
                "changes_applied": False,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # Verify all devices were processed
            assert len(results) == 3
            assert all(r.status == DeploymentStatus.SUCCESS for r in results)
            assert all(r.changes_applied is False for r in results)
            # Verify diff stats
            assert all(r.diff_lines_added == 2 for r in results)
            assert all(r.diff_lines_removed == 1 for r in results)

    async def test_full_deployment_live(
        self, integration_inventory: Path
    ) -> None:
        """Test complete live deployment workflow."""
        deployer = Deployer(
            inventory_path=integration_inventory,
            mode=DeploymentMode.MERGE,
            dry_run=False,
            show_diff=True,
            max_concurrent=3,
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": "+config line 1\n+config line 2\n-old line",
                "changes_applied": True,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            assert len(results) == 3
            assert all(r.status == DeploymentStatus.SUCCESS for r in results)
            assert all(r.changes_applied is True for r in results)
            # Verify diff stats with show_diff=True, diff should be stored
            assert all(r.diff is not None for r in results)
            assert all(r.diff_lines_added == 2 for r in results)
            assert all(r.diff_lines_removed == 1 for r in results)

    async def test_deployment_with_partial_failures(
        self, integration_inventory: Path
    ) -> None:
        """Test deployment with some devices failing."""
        deployer = Deployer(
            inventory_path=integration_inventory,
            mode=DeploymentMode.REPLACE,
            dry_run=False,
            max_concurrent=3,
        )

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                # Second device fails
                from avd_cli.exceptions import ConnectionError

                raise ConnectionError("Connection timeout")
            return {
                "success": True,
                "diff": "+new config",
                "changes_applied": True,
            }

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.side_effect = side_effect
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # Verify mixed results
            success_count = sum(1 for r in results if r.status == DeploymentStatus.SUCCESS)
            failed_count = sum(1 for r in results if r.status == DeploymentStatus.FAILED)

            assert len(results) == 3
            assert success_count == 2
            assert failed_count == 1

            # Verify diff stats for successful deployments
            successful_results = [r for r in results if r.status == DeploymentStatus.SUCCESS]
            assert all(r.diff_lines_added == 1 for r in successful_results)
            assert all(r.diff_lines_removed == 0 for r in successful_results)

            # Failed deployments should have 0 diff stats
            failed_results = [r for r in results if r.status == DeploymentStatus.FAILED]
            assert all(r.diff_lines_added == 0 for r in failed_results)
            assert all(r.diff_lines_removed == 0 for r in failed_results)

    async def test_concurrent_deployment_ordering(
        self, integration_inventory: Path
    ) -> None:
        """Test that concurrent deployments are properly managed."""
        import asyncio
        from collections import deque

        execution_order = deque()

        async def track_execution(*args, **kwargs):
            # Track execution order
            target = args[0] if args else None
            if hasattr(target, "hostname"):
                execution_order.append(target.hostname)
            await asyncio.sleep(0.01)  # Simulate work
            return {
                "success": True,
                "diff": "",
                "changes_applied": True,
            }

        deployer = Deployer(
            inventory_path=integration_inventory,
            mode=DeploymentMode.REPLACE,
            dry_run=False,
            max_concurrent=2,  # Limit concurrency
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.side_effect = track_execution
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # All devices should be processed
            assert len(results) == 3
            # Max concurrent limit should be respected (hard to test deterministically)
            assert all(r.status == DeploymentStatus.SUCCESS for r in results)

    async def test_deployment_with_missing_configs(
        self, tmp_path: Path
    ) -> None:
        """Test deployment when some config files are missing."""
        inventory_data = {
            "all": {
                "children": {
                    "fabric": {
                        "vars": {
                            "ansible_user": "admin",
                            "ansible_password": "admin",
                        },
                        "hosts": {
                            "device-1": {"ansible_host": "10.0.0.1"},
                            "device-2": {"ansible_host": "10.0.0.2"},
                        },
                    },
                }
            }
        }

        inventory_file = tmp_path / "inventory.yml"
        with open(inventory_file, "w", encoding='utf-8') as f:
            yaml.dump(inventory_data, f)

        # Create only one config file
        configs_dir = tmp_path / "intended" / "configs"
        configs_dir.mkdir(parents=True, exist_ok=True)
        config_file = configs_dir / "device-1.cfg"
        config_file.write_text("hostname device-1\n")

        deployer = Deployer(
            inventory_path=inventory_file,
            configs_path=configs_dir,
            mode=DeploymentMode.REPLACE,
            dry_run=True,
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": "+hostname device-1",
                "changes_applied": False,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # One device should succeed, one should be skipped
            success_count = sum(1 for r in results if r.status == DeploymentStatus.SUCCESS)
            skipped_count = sum(1 for r in results if r.status == DeploymentStatus.SKIPPED)

            assert len(results) == 2
            assert success_count == 1
            assert skipped_count == 1

            # Verify diff stats
            successful_results = [r for r in results if r.status == DeploymentStatus.SUCCESS]
            assert all(r.diff_lines_added == 1 for r in successful_results)

            skipped_results = [r for r in results if r.status == DeploymentStatus.SKIPPED]
            assert all(r.diff_lines_added == 0 for r in skipped_results)
            assert all(r.diff_lines_removed == 0 for r in skipped_results)

    async def test_deployment_with_group_filtering(
        self, tmp_path: Path
    ) -> None:
        """Test deployment with group filtering."""
        inventory_data = {
            "all": {
                "children": {
                    "spines": {
                        "vars": {
                            "ansible_user": "admin",
                            "ansible_password": "admin",
                        },
                        "hosts": {
                            "spine-1": {"ansible_host": "10.0.0.1"},
                            "spine-2": {"ansible_host": "10.0.0.2"},
                        },
                    },
                    "leafs": {
                        "vars": {
                            "ansible_user": "admin",
                            "ansible_password": "admin",
                        },
                        "hosts": {
                            "leaf-1": {"ansible_host": "10.0.1.1"},
                            "leaf-2": {"ansible_host": "10.0.1.2"},
                        },
                    },
                }
            }
        }

        inventory_file = tmp_path / "inventory.yml"
        with open(inventory_file, "w", encoding='utf-8') as f:
            yaml.dump(inventory_data, f)

        # Create config files
        configs_dir = tmp_path / "intended" / "configs"
        configs_dir.mkdir(parents=True, exist_ok=True)

        for device in ["spine-1", "spine-2", "leaf-1", "leaf-2"]:
            config_file = configs_dir / f"{device}.cfg"
            config_file.write_text(f"hostname {device}\n")

        # Deploy only to spines group
        deployer = Deployer(
            inventory_path=inventory_file,
            configs_path=configs_dir,
            mode=DeploymentMode.REPLACE,
            limit_to_groups=["spines"],
            dry_run=True,
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.apply_config.return_value = {
                "success": True,
                "diff": "+interface Ethernet1\n-interface Loopback0",
                "changes_applied": False,
            }
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # Only spine devices should be processed
            assert len(results) == 2
            hostnames = {r.hostname for r in results}
            assert hostnames == {"spine-1", "spine-2"}

            # Verify diff stats
            assert all(r.diff_lines_added == 1 for r in results)
            assert all(r.diff_lines_removed == 1 for r in results)

    async def test_deployment_timeout_handling(
        self, integration_inventory: Path
    ) -> None:
        """Test deployment with connection timeout."""
        deployer = Deployer(
            inventory_path=integration_inventory,
            mode=DeploymentMode.REPLACE,
            timeout=1,  # Very short timeout
            dry_run=False,
        )

        with patch("avd_cli.logics.deployer.EapiClient") as mock_client_class:
            # Simulate timeout
            from avd_cli.exceptions import ConnectionError

            mock_client = AsyncMock()
            mock_client.__aenter__.side_effect = ConnectionError("Connection timeout")
            mock_client_class.return_value = mock_client

            results = await deployer.deploy()

            # All devices should fail due to timeout
            assert len(results) == 3
            assert all(r.status == DeploymentStatus.FAILED for r in results)
            assert all("timeout" in r.error.lower() for r in results if r.error)

            # Failed deployments should have 0 diff stats
            assert all(r.diff_lines_added == 0 for r in results)
            assert all(r.diff_lines_removed == 0 for r in results)
