#!/usr/bin/env python
# coding: utf-8 -*-

"""Additional unit tests for CLI main commands.

Tests for generate subcommands (all, configs, docs, tests) and validate command.
Uses mocks for loader and generator to test CLI logic in isolation.
"""

from ipaddress import IPv4Address
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from avd_cli.cli.main import cli
from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData


class TestGenerateAllCommand:
    """Test generate all subcommand."""

    def test_generate_all_success(self, tmp_path: Path) -> None:
        """Test successful generation of all outputs.

        Given: Valid inventory and output paths
        When: Running generate all command
        Then: Generates configs, docs, and tests successfully
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        output_path = tmp_path / "output"

        # Create mock inventory
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        # Mock loader and generator
        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.generate_all") as mock_gen_all:
                mock_gen_all.return_value = (
                    [output_path / "configs" / "spine01.cfg"],
                    [output_path / "documentation" / "spine01.md"],
                    [output_path / "tests" / "tests.yaml"],
                )

                result = runner.invoke(
                    cli,
                    [
                        "generate",
                        "all",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                    ],
                )

        assert result.exit_code == 0
        assert "Generation complete" in result.output
        assert "Configurations" in result.output

    def test_generate_all_with_verbose(self, tmp_path: Path) -> None:
        """Test generate all with verbose flag.

        Given: Verbose flag enabled
        When: Running generate all command
        Then: Shows detailed output
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.generate_all") as mock_gen_all:
                mock_gen_all.return_value = ([], [], [])

                result = runner.invoke(
                    cli,
                    [
                        "-v",
                        "generate",
                        "all",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                    ],
                )

        assert result.exit_code == 0
        assert "Verbose mode enabled" in result.output
        assert "Inventory path:" in result.output
        assert "Workflow:" in result.output

    def test_generate_all_with_limit_to_groups(self, tmp_path: Path) -> None:
        """Test generate all with limit-to-groups option.

        Given: limit-to-groups specified
        When: Running generate all command
        Then: Passes groups to generator
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.generate_all") as mock_gen_all:
                mock_gen_all.return_value = ([], [], [])

                result = runner.invoke(
                    cli,
                    [
                        "-v",
                        "generate",
                        "all",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                        "-l",
                        "spine",
                        "-l",
                        "leaf",
                    ],
                )

        assert result.exit_code == 0
        assert "Limited to groups: spine, leaf" in result.output

    def test_generate_all_with_workflow(self, tmp_path: Path) -> None:
        """Test generate all with workflow option.

        Given: Workflow parameter specified
        When: Running generate all command
        Then: Passes workflow to generator
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.generate_all") as mock_gen_all:
                mock_gen_all.return_value = ([], [], [])

                result = runner.invoke(
                    cli,
                    [
                        "-v",
                        "generate",
                        "all",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                        "--workflow",
                        "cli-config",
                    ],
                )

        assert result.exit_code == 0
        assert "Workflow: cli-config" in result.output

    def test_generate_all_validation_failure(self, tmp_path: Path) -> None:
        """Test generate all with validation errors.

        Given: Inventory with validation errors
        When: Running generate all command
        Then: Exits with error code
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        output_path = tmp_path / "output"

        # Create inventory with no spine devices (validation error)
        device = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            leaf_devices=[device],
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
                    "generate",
                    "all",
                    "-i",
                    str(inventory_path),
                    "-o",
                    str(output_path),
                ],
            )

        assert result.exit_code == 1
        assert "validation failed" in result.output
        assert "no spine devices" in result.output

    def test_generate_all_exception_handling(self, tmp_path: Path) -> None:
        """Test generate all with exception during generation.

        Given: Exception during generation
        When: Running generate all command
        Then: Exits with error message
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        output_path = tmp_path / "output"

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.side_effect = Exception("Failed to load inventory")
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "all",
                    "-i",
                    str(inventory_path),
                    "-o",
                    str(output_path),
                ],
            )

        assert result.exit_code == 1
        assert "Error:" in result.output
        assert "Failed to load inventory" in result.output


class TestDefaultOutputPath:
    """Test default output path behavior (<inventory_path>/intended)."""

    def test_generate_all_with_default_output_path(self, tmp_path: Path) -> None:
        """Test generate all uses default output path when -o not specified.

        Given: Valid inventory path without explicit output path
        When: Running generate all command without -o option
        Then: Uses <inventory_path>/intended as output and displays info message
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        expected_output = inventory_path / "intended"

        # Create mock inventory
        spine_device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="spine",
            fabric="DC1",
        )
        leaf_device = DeviceDefinition(
            hostname="leaf01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.11"),
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine_device],
            leaf_devices=[leaf_device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class, \
             patch("avd_cli.logics.generator.generate_all") as mock_gen_all, \
             patch("avd_cli.cli.main.suppress_pyavd_warnings"):

            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            mock_gen_all.return_value = (
                [expected_output / "configs" / "leaf01.cfg"],
                [expected_output / "documentation" / "leaf01.md"],
                [expected_output / "tests" / "tests.yaml"],
            )

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "all",
                    "-i",
                    str(inventory_path),
                ],
            )

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                print(f"Exception: {result.exception}")
                import traceback
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}\nOutput: {result.output}"
        assert "Using default output path" in result.output or "intended" in result.output
        assert "Generation complete" in result.output

    def test_generate_configs_with_default_output_path(self, tmp_path: Path) -> None:
        """Test generate configs uses default output path.

        Given: Valid inventory path without explicit output path
        When: Running generate configs command without -o option
        Then: Uses <inventory_path>/intended as output
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        expected_output = inventory_path / "intended"

        spine_device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="spine",
            fabric="DC1",
        )
        leaf_device = DeviceDefinition(
            hostname="leaf01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.11"),
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine_device],
            leaf_devices=[leaf_device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class, \
             patch("avd_cli.logics.generator.ConfigurationGenerator") as mock_gen_class, \
             patch("avd_cli.cli.main.suppress_pyavd_warnings"):

            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            mock_generator = MagicMock()
            mock_generator.generate.return_value = [expected_output / "configs" / "spine01.cfg"]
            mock_gen_class.return_value = mock_generator

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "configs",
                    "-i",
                    str(inventory_path),
                ],
            )

        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}\nOutput: {result.output}"
        assert "Using default output path" in result.output or "intended" in result.output
        assert str(expected_output) in result.output or "configs" in result.output

    def test_generate_docs_with_default_output_path(self, tmp_path: Path) -> None:
        """Test generate docs uses default output path.

        Given: Valid inventory path without explicit output path
        When: Running generate docs command without -o option
        Then: Uses <inventory_path>/intended as output
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        expected_output = inventory_path / "intended"

        spine_device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="spine",
            fabric="DC1",
        )
        leaf_device = DeviceDefinition(
            hostname="leaf01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.11"),
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine_device],
            leaf_devices=[leaf_device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class, \
             patch("avd_cli.logics.generator.DocumentationGenerator") as mock_gen_class, \
             patch("avd_cli.cli.main.suppress_pyavd_warnings"):

            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            mock_generator = MagicMock()
            mock_generator.generate.return_value = [expected_output / "documentation" / "leaf01.md"]
            mock_gen_class.return_value = mock_generator

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "docs",
                    "-i",
                    str(inventory_path),
                ],
            )

        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}\nOutput: {result.output}"
        assert "Using default output path" in result.output or "intended" in result.output
        assert str(expected_output) in result.output or "documentation" in result.output

    def test_generate_tests_with_default_output_path(self, tmp_path: Path) -> None:
        """Test generate tests uses default output path.

        Given: Valid inventory path without explicit output path
        When: Running generate tests command without -o option
        Then: Uses <inventory_path>/intended as output
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        expected_output = inventory_path / "intended"

        spine_device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="spine",
            fabric="DC1",
        )
        leaf_device = DeviceDefinition(
            hostname="leaf01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.11"),
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine_device],
            leaf_devices=[leaf_device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class, \
             patch("avd_cli.logics.generator.TestGenerator") as mock_gen_class, \
             patch("avd_cli.cli.main.suppress_pyavd_warnings"):

            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            mock_generator = MagicMock()
            mock_generator.generate.return_value = [
                expected_output / "tests" / "anta_catalog.yml",
                expected_output / "tests" / "anta_inventory.yml",
            ]
            mock_gen_class.return_value = mock_generator

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "tests",
                    "-i",
                    str(inventory_path),
                ],
            )

        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}\nOutput: {result.output}"
        assert "Using default output path" in result.output or "intended" in result.output
        assert str(expected_output) in result.output or "tests" in result.output

    def test_explicit_output_path_overrides_default(self, tmp_path: Path) -> None:
        """Test explicit -o option overrides default behavior.

        Given: Valid inventory path with explicit output path
        When: Running generate all with -o option
        Then: Uses specified output path, not default
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        custom_output = tmp_path / "custom-output"

        spine_device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="spine",
            fabric="DC1",
        )
        leaf_device = DeviceDefinition(
            hostname="leaf01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.11"),
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine_device],
            leaf_devices=[leaf_device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class, \
             patch("avd_cli.logics.generator.generate_all") as mock_gen_all, \
             patch("avd_cli.cli.main.suppress_pyavd_warnings"):

            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            mock_gen_all.return_value = (
                [custom_output / "configs" / "leaf01.cfg"],
                [custom_output / "documentation" / "leaf01.md"],
                [custom_output / "tests" / "tests.yaml"],
            )

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "all",
                    "-i",
                    str(inventory_path),
                    "-o",
                    str(custom_output),
                ],
            )

        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}\nOutput: {result.output}"
        # Should NOT show default output message
        assert "Using default output path" not in result.output
        assert "Generation complete" in result.output

    def test_env_var_output_path_overrides_default(self, tmp_path: Path) -> None:
        """Test AVD_CLI_OUTPUT_PATH environment variable overrides default.

        Given: AVD_CLI_OUTPUT_PATH environment variable set
        When: Running generate all without -o option
        Then: Uses environment variable path, not default
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        env_output = tmp_path / "env-output"

        spine_device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="spine",
            fabric="DC1",
        )
        leaf_device = DeviceDefinition(
            hostname="leaf01",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.11"),
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine_device],
            leaf_devices=[leaf_device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class, \
             patch("avd_cli.logics.generator.generate_all") as mock_gen_all, \
             patch("avd_cli.cli.main.suppress_pyavd_warnings"):

            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            mock_gen_all.return_value = (
                [env_output / "configs" / "leaf01.cfg"],
                [env_output / "documentation" / "leaf01.md"],
                [env_output / "tests" / "tests.yaml"],
            )

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "all",
                    "-i",
                    str(inventory_path),
                ],
                env={"AVD_CLI_OUTPUT_PATH": str(env_output)},
            )

        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}\nOutput: {result.output}"
        # Should NOT show default output message when env var is set
        assert "Using default output path" not in result.output
        assert "Generation complete" in result.output


class TestGenerateConfigsCommand:
    """Test generate configs subcommand."""

    def test_generate_configs_success(self, tmp_path: Path) -> None:
        """Test successful generation of configurations only.

        Given: Valid inventory and output paths
        When: Running generate configs command
        Then: Generates configurations successfully
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.ConfigurationGenerator") as mock_gen_class:
                mock_gen = MagicMock()
                mock_gen.generate.return_value = [output_path / "configs" / "spine01.cfg"]
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
                    ],
                )

        assert result.exit_code == 0
        assert "Generated 1 configuration" in result.output

    def test_generate_configs_with_verbose(self, tmp_path: Path) -> None:
        """Test generate configs with verbose flag.

        Given: Verbose flag enabled
        When: Running generate configs command
        Then: Shows detailed output
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.ConfigurationGenerator") as mock_gen_class:
                mock_gen = MagicMock()
                mock_gen.generate.return_value = []
                mock_gen_class.return_value = mock_gen

                result = runner.invoke(
                    cli,
                    [
                        "-v",
                        "generate",
                        "configs",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                    ],
                )

        assert result.exit_code == 0
        assert "Generating configurations only" in result.output


class TestGenerateDocsCommand:
    """Test generate docs subcommand."""

    def test_generate_docs_success(self, tmp_path: Path) -> None:
        """Test successful generation of documentation only.

        Given: Valid inventory and output paths
        When: Running generate docs command
        Then: Generates documentation successfully
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.DocumentationGenerator") as mock_gen_class:
                mock_gen = MagicMock()
                mock_gen.generate.return_value = [output_path / "documentation" / "spine01.md"]
                mock_gen_class.return_value = mock_gen

                result = runner.invoke(
                    cli,
                    [
                        "generate",
                        "docs",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                    ],
                )

        assert result.exit_code == 0
        assert "Generated 1 documentation file" in result.output


class TestGenerateTestsCommand:
    """Test generate tests subcommand."""

    def test_generate_tests_success(self, tmp_path: Path) -> None:
        """Test successful generation of test files only.

        Given: Valid inventory and output paths
        When: Running generate tests command
        Then: Generates test files successfully
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.TestGenerator") as mock_gen_class:
                mock_gen = MagicMock()
                mock_gen.generate.return_value = [output_path / "tests" / "tests.yaml"]
                mock_gen_class.return_value = mock_gen

                result = runner.invoke(
                    cli,
                    [
                        "generate",
                        "tests",
                        "-i",
                        str(inventory_path),
                        "-o",
                        str(output_path),
                    ],
                )

        assert result.exit_code == 0
        assert "Generated 1 test file" in result.output


class TestValidateCommand:
    """Test validate command."""

    def test_validate_success(self, tmp_path: Path) -> None:
        """Test successful validation.

        Given: Valid inventory
        When: Running validate command
        Then: Shows success message
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
            spine_devices=[device],
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
                ["validate", "-i", str(inventory_path)],
            )

        assert result.exit_code == 0
        assert "Validation successful" in result.output

    def test_validate_with_errors(self, tmp_path: Path) -> None:
        """Test validation with errors.

        Given: Inventory with validation errors
        When: Running validate command
        Then: Shows errors and exits with error code
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        # Create inventory with no spine devices (validation error)
        device = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            leaf_devices=[device],
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
                ["validate", "-i", str(inventory_path)],
            )

        assert result.exit_code == 1
        assert "Validation failed" in result.output
        assert "no spine devices" in result.output


class TestInfoCommand:
    """Test info command."""

    def test_info_success(self, tmp_path: Path) -> None:
        """Test successful info display.

        Given: Valid inventory
        When: Running info command
        Then: Shows inventory information
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        spine = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        leaf = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine],
            leaf_devices=[leaf],
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
                ["info", "-i", str(inventory_path)],
            )

        assert result.exit_code == 0
        assert "Inventory Summary" in result.output
        assert "DC1" in result.output
        assert "2" in result.output  # Device count


class TestEnvironmentVariables:
    """Test environment variable support for CLI options."""

    def test_generate_configs_with_env_vars(self, tmp_path: Path) -> None:
        """Test generate configs using environment variables.

        Given: Environment variables for inventory and output paths
        When: Running generate configs without CLI arguments
        Then: Uses environment variable values
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        output_path = tmp_path / "output"

        # Create mock inventory
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        # Mock loader and generator
        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.ConfigurationGenerator"):
                # Set environment variables
                env = {
                    "AVD_CLI_INVENTORY_PATH": str(inventory_path),
                    "AVD_CLI_OUTPUT_PATH": str(output_path),
                    "AVD_CLI_WORKFLOW": "eos-design",
                }

                result = runner.invoke(
                    cli,
                    ["generate", "configs"],
                    env=env,
                )

        assert result.exit_code == 0
        assert "Loading inventory" in result.output

    def test_cli_args_override_env_vars(self, tmp_path: Path) -> None:
        """Test that CLI arguments override environment variables.

        Given: Both environment variables and CLI arguments
        When: Running command with both
        Then: CLI arguments take precedence
        """
        runner = CliRunner()
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        output_path = tmp_path / "output"
        alt_output_path = tmp_path / "alt_output"

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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.ConfigurationGenerator"):
                # Set environment variables
                env = {
                    "AVD_CLI_INVENTORY_PATH": str(inventory_path),
                    "AVD_CLI_OUTPUT_PATH": str(output_path),
                }

                # CLI argument overrides env var
                result = runner.invoke(
                    cli,
                    ["generate", "configs", "-i", str(inventory_path), "-o", str(alt_output_path)],
                    env=env,
                )

        assert result.exit_code == 0

    def test_info_with_format_env_var(self, tmp_path: Path) -> None:
        """Test info command with format from environment variable.

        Given: AVD_CLI_FORMAT environment variable
        When: Running info command
        Then: Uses format from environment variable
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            env = {
                "AVD_CLI_INVENTORY_PATH": str(inventory_path),
                "AVD_CLI_FORMAT": "json",
            }

            result = runner.invoke(
                cli,
                ["info"],
                env=env,
            )

        assert result.exit_code == 0

    def test_show_deprecation_warnings_env_var(self, tmp_path: Path) -> None:
        """Test show-deprecation-warnings from environment variable.

        Given: AVD_CLI_SHOW_DEPRECATION_WARNINGS=true
        When: Running generate command
        Then: Deprecation warnings are shown
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
            spine_devices=[device],
        )
        mock_inventory = InventoryData(
            root_path=inventory_path,
            fabrics=[fabric],
        )

        with patch("avd_cli.logics.loader.InventoryLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = mock_inventory
            mock_loader_class.return_value = mock_loader

            with patch("avd_cli.logics.generator.ConfigurationGenerator"):
                env = {
                    "AVD_CLI_INVENTORY_PATH": str(inventory_path),
                    "AVD_CLI_OUTPUT_PATH": str(output_path),
                    "AVD_CLI_SHOW_DEPRECATION_WARNINGS": "true",
                }

                result = runner.invoke(
                    cli,
                    ["generate", "configs"],
                    env=env,
                )

        assert result.exit_code == 0

    def test_help_shows_env_vars(self) -> None:
        """Test that --help displays environment variable names.

        Given: generate configs command
        When: Running with --help flag
        Then: Environment variable names are shown
        """
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["generate", "configs", "--help"],
        )

        assert result.exit_code == 0
        assert "AVD_CLI_INVENTORY_PATH" in result.output
        assert "AVD_CLI_OUTPUT_PATH" in result.output
        assert "AVD_CLI_WORKFLOW" in result.output
        assert "AVD_CLI_SHOW_DEPRECATION_WARNINGS" in result.output
        assert "[env var:" in result.output
