#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for generate command module."""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Seed missing command modules to satisfy package imports
sys.modules.setdefault("avd_cli.cli.commands.deploy", ModuleType("avd_cli.cli.commands.deploy"))
sys.modules.setdefault("avd_cli.cli.commands.validate", ModuleType("avd_cli.cli.commands.validate"))

# pylint: disable=wrong-import-position  # Import after sys.modules setup
from avd_cli.cli.commands.generate import (  # noqa: E402
    generate,
    generate_all,
    generate_configs,
    generate_docs,
    generate_tests,
)


@pytest.fixture
def mock_inventory_setup():
    """Setup mock inventory and loader for tests."""
    # Mock device
    device = MagicMock()
    device.hostname = "spine-01"
    device.device_type = "spine"
    device.groups = ["SPINES"]
    device.fabric = "DC1"

    # Mock inventory
    inventory = MagicMock()
    inventory.get_all_devices.return_value = [device]
    inventory.validate.return_value = []

    # Mock loader
    loader = MagicMock()
    loader.load.return_value = inventory

    return device, inventory, loader


class TestGenerateGroup:
    """Test suite for generate command group."""

    def test_generate_help(self):
        """Test generate command group help."""
        runner = CliRunner()
        result = runner.invoke(generate, ["--help"])

        assert result.exit_code == 0
        assert "all" in result.output.lower() or "generate" in result.output.lower()


class TestGenerateAllCommand:
    """Test suite for generate all command."""

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.generate_all")
    @patch("avd_cli.cli.commands.generate.normalize_workflow")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    def test_generate_all_success(
        self, mock_resolve, mock_normalize, mock_gen_all, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test successful generation of all outputs."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_gen_all.return_value = (["config1.cfg"], ["doc1.md"], ["test1.yaml"])
        mock_normalize.return_value = "eos-design"
        mock_resolve.return_value = tmp_path / "output"

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_all,
            [
                "--inventory-path",
                str(inventory_path),
                "--output-path",
                str(tmp_path / "output"),
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0
        mock_gen_all.assert_called_once()

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    def test_generate_all_validation_failure(
        self, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test generate all with validation errors."""
        _device, inventory, loader = mock_inventory_setup
        inventory.validate.return_value = ["Error: Invalid device"]
        mock_loader_class.return_value = loader

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_all,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code != 0
        assert "validation failed" in result.output.lower()

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.generate_all")
    @patch("avd_cli.cli.commands.generate.normalize_workflow")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    def test_generate_all_with_limit_patterns(
        self, mock_resolve, mock_normalize, mock_gen_all, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test generate all with limit patterns."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_gen_all.return_value = (["config1.cfg"], [], [])
        mock_normalize.return_value = "eos-design"
        mock_resolve.return_value = tmp_path / "output"

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_all,
            [
                "--inventory-path",
                str(inventory_path),
                "--limit",
                "spine-*",
            ],
            obj={"verbose": True},
        )

        assert result.exit_code == 0

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.generate_all")
    @patch("avd_cli.cli.commands.generate.normalize_workflow")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    def test_generate_all_with_workflow(
        self, mock_resolve, mock_normalize, mock_gen_all, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test generate all with custom workflow."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_gen_all.return_value = (["config1.cfg"], [], [])
        mock_normalize.return_value = "cli-config"
        mock_resolve.return_value = tmp_path / "output"

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_all,
            [
                "--inventory-path",
                str(inventory_path),
                "--workflow",
                "cli-config",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.generate_all")
    @patch("avd_cli.cli.commands.generate.normalize_workflow")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    def test_generate_all_exception_handling(
        self, mock_resolve, mock_normalize, mock_gen_all, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test exception handling in generate all."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_gen_all.side_effect = RuntimeError("Generation failed")
        mock_normalize.return_value = "eos-design"
        mock_resolve.return_value = tmp_path / "output"

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_all,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower()


class TestGenerateConfigsCommand:
    """Test suite for generate configs command."""

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.ConfigurationGenerator")
    @patch("avd_cli.cli.commands.generate.normalize_workflow")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_configs_success(
        self, mock_display, mock_resolve, mock_normalize, mock_gen_class,
        mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test successful config generation."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_normalize.return_value = "eos-design"
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.return_value = ["config1.cfg", "config2.cfg"]
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_configs,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code == 0
        mock_generator.generate.assert_called_once()

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    def test_generate_configs_validation_failure(
        self, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test config generation with validation errors."""
        _device, inventory, loader = mock_inventory_setup
        inventory.validate.return_value = ["Error: Invalid config"]
        mock_loader_class.return_value = loader

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_configs,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code != 0

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.ConfigurationGenerator")
    @patch("avd_cli.cli.commands.generate.normalize_workflow")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_configs_with_workflow(
        self, mock_display, mock_resolve, mock_normalize, mock_gen_class,
        mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test config generation with custom workflow."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_normalize.return_value = "cli-config"
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.return_value = ["config1.cfg"]
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_configs,
            [
                "--inventory-path",
                str(inventory_path),
                "--workflow",
                "cli-config",
            ],
            obj={"verbose": True},
        )

        assert result.exit_code == 0


class TestGenerateDocsCommand:
    """Test suite for generate docs command."""

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.DocumentationGenerator")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_docs_success(
        self, mock_display, mock_resolve, mock_gen_class, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test successful documentation generation."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.return_value = ["doc1.md", "doc2.md"]
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_docs,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code == 0
        mock_generator.generate.assert_called_once()

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.DocumentationGenerator")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_docs_with_limit(
        self, mock_display, mock_resolve, mock_gen_class, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test docs generation with device filter."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.return_value = ["doc1.md"]
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_docs,
            [
                "--inventory-path",
                str(inventory_path),
                "--limit",
                "spine-*",
            ],
            obj={"verbose": True},
        )

        assert result.exit_code == 0

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.DocumentationGenerator")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_docs_exception_handling(
        self, mock_display, mock_resolve, mock_gen_class, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test exception handling in docs generation."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.side_effect = RuntimeError("Doc generation failed")
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_docs,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code != 0


class TestGenerateTestsCommand:
    """Test suite for generate tests command."""

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.TestGenerator")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_tests_success(
        self, mock_display, mock_resolve, mock_gen_class, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test successful test generation."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.return_value = ["test1.yaml"]
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_tests,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code == 0
        mock_generator.generate.assert_called_once()

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.TestGenerator")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_tests_with_type(
        self, mock_display, mock_resolve, mock_gen_class, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test test generation with custom type."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.return_value = ["test1.robot"]
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_tests,
            [
                "--inventory-path",
                str(inventory_path),
                "--test-type",
                "robot",
            ],
            obj={"verbose": True},
        )

        assert result.exit_code == 0

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.TestGenerator")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_tests_with_limit(
        self, mock_display, mock_resolve, mock_gen_class, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test test generation with device filter."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.return_value = ["test1.yaml"]
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_tests,
            [
                "--inventory-path",
                str(inventory_path),
                "--limit",
                "spine-*",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0

    @patch("avd_cli.cli.commands.generate.InventoryLoader")
    @patch("avd_cli.logics.generator.TestGenerator")
    @patch("avd_cli.cli.commands.generate.resolve_output_path")
    @patch("avd_cli.cli.commands.generate.display_generation_summary")
    def test_generate_tests_exception_handling(
        self, mock_display, mock_resolve, mock_gen_class, mock_loader_class, mock_inventory_setup, tmp_path
    ):
        """Test exception handling in test generation."""
        _device, _inventory, loader = mock_inventory_setup
        mock_loader_class.return_value = loader
        mock_resolve.return_value = tmp_path / "output"

        mock_generator = MagicMock()
        mock_generator.generate.side_effect = RuntimeError("Test generation failed")
        mock_gen_class.return_value = mock_generator

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            generate_tests,
            ["--inventory-path", str(inventory_path)],
            obj={"verbose": False},
        )

        assert result.exit_code != 0
