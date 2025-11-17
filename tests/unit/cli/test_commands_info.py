#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for info command module."""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Seed missing command modules to satisfy package imports
sys.modules.setdefault("avd_cli.cli.commands.deploy", ModuleType("avd_cli.cli.commands.deploy"))
sys.modules.setdefault("avd_cli.cli.commands.validate", ModuleType("avd_cli.cli.commands.validate"))

# pylint: disable=wrong-import-position  # Import after sys.modules setup
from avd_cli.cli.commands.info import _gather_inventory_data, _print_table, info  # noqa: E402


class TestInfoCommand:
    """Test suite for info command."""

    @pytest.fixture
    def mock_inventory(self):
        """Create a mock inventory for testing."""
        # Mock device
        device1 = MagicMock()
        device1.hostname = "spine-01"
        device1.device_type = "spine"
        device1.platform = "vEOS-lab"
        device1.mgmt_ip = "192.168.0.10"
        device1.fabric = "DC1"
        device1.groups = ["SPINES", "DC1"]

        device2 = MagicMock()
        device2.hostname = "leaf-01"
        device2.device_type = "leaf"
        device2.platform = "vEOS-lab"
        device2.mgmt_ip = "192.168.0.20"
        device2.fabric = "DC1"
        device2.groups = ["LEAVES", "DC1"]

        # Mock fabric
        fabric = MagicMock()
        fabric.name = "DC1"
        fabric.design_type = "l3ls-evpn"
        fabric.spine_devices = [device1]
        fabric.leaf_devices = [device2]
        fabric.border_leaf_devices = []
        fabric.get_all_devices.return_value = [device1, device2]

        # Mock inventory
        inventory = MagicMock()
        inventory.fabrics = [fabric]
        inventory.get_all_devices.return_value = [device1, device2]

        return inventory

    @patch("avd_cli.cli.commands.info.InventoryLoader")
    def test_info_table_format(self, mock_loader_class, mock_inventory, tmp_path):
        """Test info command with table format."""
        # Setup
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_inventory
        mock_loader_class.return_value = mock_loader

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            info,
            ["--inventory-path", str(inventory_path), "--format", "table"],
            obj={"verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "spine-01" in result.output
        assert "leaf-01" in result.output
        assert "DC1" in result.output
        mock_loader.load.assert_called_once()

    @patch("avd_cli.cli.commands.info.InventoryLoader")
    def test_info_json_format(self, mock_loader_class, mock_inventory, tmp_path):
        """Test info command with JSON format."""
        # Setup
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_inventory
        mock_loader_class.return_value = mock_loader

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            info,
            ["--inventory-path", str(inventory_path), "--format", "json"],
            obj={"verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "spine-01" in result.output
        assert "total_devices" in result.output
        mock_loader.load.assert_called_once()

    @patch("avd_cli.cli.commands.info.InventoryLoader")
    def test_info_yaml_format(self, mock_loader_class, mock_inventory, tmp_path):
        """Test info command with YAML format."""
        # Setup
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_inventory
        mock_loader_class.return_value = mock_loader

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            info,
            ["--inventory-path", str(inventory_path), "--format", "yaml"],
            obj={"verbose": False},
        )

        # Verify
        assert result.exit_code == 0
        assert "spine-01" in result.output or "spine_01" in result.output
        mock_loader.load.assert_called_once()

    @patch("avd_cli.cli.commands.info.InventoryLoader")
    def test_info_verbose_mode(self, mock_loader_class, mock_inventory, tmp_path):
        """Test info command with verbose flag."""
        # Setup
        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_inventory
        mock_loader_class.return_value = mock_loader

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            info,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": True},
        )

        # Verify
        assert result.exit_code == 0
        mock_loader.load.assert_called_once()

    @patch("avd_cli.cli.commands.info.InventoryLoader")
    def test_info_with_error(self, mock_loader_class, tmp_path):
        """Test info command when loader raises error."""
        # Setup
        mock_loader = MagicMock()
        mock_loader.load.side_effect = ValueError("Invalid inventory")
        mock_loader_class.return_value = mock_loader

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            info,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        # Verify
        assert result.exit_code != 0

    def test_print_table(self, mock_inventory, tmp_path, capsys):
        """Test _print_table helper function."""
        with patch("avd_cli.cli.commands.info.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            inventory_path = tmp_path / "inventory"
            inventory_path.mkdir()

            _print_table(inventory_path)

            mock_loader.load.assert_called_once_with(inventory_path)

    def test_gather_inventory_data(self, mock_inventory, tmp_path):
        """Test _gather_inventory_data helper function."""
        with patch("avd_cli.cli.commands.info.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            inventory_path = tmp_path / "inventory"
            inventory_path.mkdir()

            data = _gather_inventory_data(inventory_path)

            assert data["total_devices"] == 2
            assert data["total_fabrics"] == 1
            assert len(data["fabrics"]) == 1
            assert data["fabrics"][0]["name"] == "DC1"
            assert data["fabrics"][0]["spine_devices"] == 1
            assert data["fabrics"][0]["leaf_devices"] == 1
            assert len(data["fabrics"][0]["devices"]) == 2

    def test_gather_inventory_data_empty_fabric(self, tmp_path):
        """Test _gather_inventory_data with empty fabric."""
        with patch("avd_cli.cli.commands.info.InventoryLoader") as mock_loader_class:
            # Mock empty fabric
            fabric = MagicMock()
            fabric.name = "EMPTY"
            fabric.design_type = "l3ls-evpn"
            fabric.spine_devices = []
            fabric.leaf_devices = []
            fabric.border_leaf_devices = []
            fabric.get_all_devices.return_value = []

            inventory = MagicMock()
            inventory.fabrics = [fabric]
            inventory.get_all_devices.return_value = []

            mock_loader = MagicMock()
            mock_loader.load.return_value = inventory
            mock_loader_class.return_value = mock_loader

            inventory_path = tmp_path / "inventory"
            inventory_path.mkdir()

            data = _gather_inventory_data(inventory_path)

            assert data["total_devices"] == 0
            assert data["total_fabrics"] == 1
            assert len(data["fabrics"][0]["devices"]) == 0
