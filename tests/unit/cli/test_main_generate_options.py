#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for generate command options to improve main.py coverage.

Focus on testing command-line options and flags for generate command variants.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from avd_cli.cli.main import cli
from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData


class TestGenerateConfigsWithLimitGroups:
    """Test generate configs with --limit-to-groups option."""

    def test_limit_to_groups_single_group(self, tmp_path: Path) -> None:
        """Test generate configs with --limit-to-groups option.

        Coverage: main.py lines 531-535 (limit_to_groups parsing and splitting)
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        output_path = tmp_path / "output"

        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
            groups=["DC1_SPINES", "FABRIC"],
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            devices_by_type={
                "spine": [device],
            },
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.cli.commands.generate.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.ConfigurationGenerator") as mock_gen_class:
                mock_gen = MagicMock()
                mock_gen.generate.return_value = {"spine01": "/path/to/config"}
                mock_gen_class.return_value = mock_gen

                result = runner.invoke(
                    cli,
                    [
                        "generate",
                        "configs",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                        "--limit-to-groups",
                        "DC1_SPINES",
                    ],
                )

        assert result.exit_code == 0


class TestGenerateWorkflowVariants:
    """Test generate command with different workflow values."""

    def test_generate_with_cli_config_workflow(self, tmp_path: Path) -> None:
        """Test generate with cli-config workflow.

        Coverage: main.py lines 469-472 (skip_topology validation for cli-config)
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        output_path = tmp_path / "output"

        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            devices_by_type={
                "spine": [device],
            },
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )
        mock_inventory.validate = MagicMock(return_value=[])

        with patch("avd_cli.cli.commands.generate.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.ConfigurationGenerator") as mock_gen_class:
                mock_gen = MagicMock()
                mock_gen.generate.return_value = {"spine01": "/path/to/config"}
                mock_gen_class.return_value = mock_gen

                result = runner.invoke(
                    cli,
                    [
                        "generate",
                        "configs",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                        "--workflow",
                        "cli-config",
                    ],
                )

        assert result.exit_code == 0
        # Verify validate was called with skip_topology=True
        mock_inventory.validate.assert_called_once_with(skip_topology_validation=True)


class TestInfoCommandFormats:
    """Test info command with different output formats."""

    def test_info_yaml_format(self, tmp_path: Path) -> None:
        """Test info command with YAML format.

        Coverage: main.py lines 913-929 (YAML output format)
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            devices_by_type={
                "spine": [device],
            },
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(
                cli,
                [
                    "info",
                    "-i",
                    str(inventory_path),
                    "--format",
                    "yaml",
                ],
            )

        assert result.exit_code == 0
        # YAML output should have some characteristic markers
        assert (":" in result.output or "-" in result.output)  # YAML structure

    def test_info_json_format(self, tmp_path: Path) -> None:
        """Test info command with JSON format.

        Coverage: main.py additional format option paths
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            devices_by_type={
                "spine": [device],
            },
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(
                cli,
                [
                    "info",
                    "-i",
                    str(inventory_path),
                    "--format",
                    "json",
                ],
            )

        assert result.exit_code == 0
        # JSON output should have characteristic markers
        assert ("{" in result.output and "}" in result.output)  # JSON structure
