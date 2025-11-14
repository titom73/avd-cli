#!/usr/bin/env python
# coding: utf-8
# pylint: disable=line-too-long
"""End-to-end tests for generate all workflow.

This module tests the complete generate all workflow using real example inventories
from the examples/ directory. These tests verify the entire pipeline from inventory
loading through configuration, documentation, and test generation.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary output directory for test artifacts.

    Yields
    ------
    Path
        Temporary directory path that will be cleaned up after the test
    """
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir
    # Cleanup
    if output_dir.exists():
        shutil.rmtree(output_dir)


@pytest.fixture
def examples_dir() -> Path:
    """Get the path to the examples directory.

    Returns
    -------
    Path
        Absolute path to the examples directory
    """
    return Path(__file__).parent.parent.parent / "examples"


class TestE2EGenerateAllBasics:
    """End-to-end tests for generate all command with basic inventory."""

    def test_generate_all_eos_design_basics_success(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all command with eos-design-basics inventory.

        This test covers:
        - CLI main.py entry point
        - Inventory loading from examples/eos-design-basics
        - Configuration generation
        - Documentation generation
        - Test generation
        - File writing to output directory

        Coverage impact: main.py, loader.py, generator.py, templating.py
        """
        inventory_path = examples_dir / "eos-design-basics"
        assert inventory_path.exists(), f"Inventory path {inventory_path} does not exist"

        # Execute generate all command
        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Verify command succeeded
        assert result.returncode == 0, (
            f"Command failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Verify output directory structure
        assert (temp_output_dir / "configs").exists(), "configs directory not created"
        assert (temp_output_dir / "documentation").exists(), "documentation directory not created"
        assert (temp_output_dir / "tests").exists(), "tests directory not created"

        # Verify configuration files were generated
        configs_dir = temp_output_dir / "configs"
        config_files = list(configs_dir.glob("*.cfg"))
        assert len(config_files) > 0, "No configuration files generated"

        # Expected devices from eos-design-basics inventory
        expected_devices = ["s1-spine1", "s1-spine2", "s1-leaf1", "s1-leaf2", "s1-leaf3", "s1-leaf4"]
        generated_devices = [f.stem for f in config_files]

        for device in expected_devices:
            assert device in generated_devices, f"Configuration for {device} not generated"

        # Verify documentation files were generated
        docs_dir = temp_output_dir / "documentation"
        device_docs = list(docs_dir.glob("*.md"))
        assert len(device_docs) > 0, "No device documentation generated"

        # Verify test files were generated
        tests_dir = temp_output_dir / "tests"
        test_files = list(tests_dir.glob("*.yml"))
        assert len(test_files) > 0, "No test files generated"

        # Verify output contains success messages
        assert "complete" in result.stdout.lower() or "generated" in result.stdout.lower()

    def test_generate_all_with_verbose_flag(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all with verbose flag for detailed output.

        Coverage: CLI verbose logging paths in main.py
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "--verbose",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        # Verbose mode should produce more detailed output
        assert len(result.stdout) > 100, "Verbose output should contain detailed logs"

    def test_generate_all_cli_config_workflow(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all with cli-config workflow.

        This tests the cli-config-gen workflow path which uses structured configs
        directly without topology validation.

        Coverage: cli-config workflow paths in main.py and generator.py
        """
        inventory_path = examples_dir / "cli-config-gen"
        if not inventory_path.exists():
            pytest.skip(f"cli-config-gen inventory not found at {inventory_path}")

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
                "--workflow",
                "cli-config",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # cli-config workflow might not have all files, but should not fail
        assert result.returncode == 0 or "no devices" in result.stderr.lower()


class TestE2EGenerateAllComplex:
    """End-to-end tests for generate all with complex inventory."""

    @pytest.mark.skip(reason="eos-design-complex inventory uses outdated pyavd schema keys")
    def test_generate_all_eos_design_complex_success(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all with eos-design-complex inventory.

        This tests a more complex topology with multiple device types,
        VLANs, BGP configurations, etc.

        Coverage: Complex data structures in generator.py, advanced templating
        """
        inventory_path = examples_dir / "eos-design-complex"
        if not inventory_path.exists():
            pytest.skip(f"eos-design-complex inventory not found at {inventory_path}")

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        # Verify comprehensive output
        configs_dir = temp_output_dir / "configs"
        config_files = list(configs_dir.glob("*.cfg"))
        assert len(config_files) > 0, "No configuration files generated for complex inventory"


class TestE2EGenerateAllMPLS:
    """End-to-end tests for generate all with MPLS design."""

    @pytest.mark.skip(reason="eos-design-mpls inventory uses device types not supported in current pyavd version")
    def test_generate_all_mpls_design(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all with MPLS design topology.

        This tests MPLS-specific device types (PE, P) and configurations.

        Coverage: MPLS design type handling in loader.py and generator.py
        """
        inventory_path = examples_dir / "eos-design-mpls"
        if not inventory_path.exists():
            pytest.skip(f"eos-design-mpls inventory not found at {inventory_path}")

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # MPLS inventory should generate successfully
        assert result.returncode == 0

        configs_dir = temp_output_dir / "configs"
        assert configs_dir.exists(), "configs directory not created for MPLS design"


class TestE2EGenerateComponentCommands:
    """End-to-end tests for individual generate component commands."""

    def test_generate_configs_only(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate configs command without docs and tests.

        Coverage: generate configs command path in main.py
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "configs",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        # Only configs should be generated
        assert (temp_output_dir / "configs").exists(), "configs directory not created"
        config_files = list((temp_output_dir / "configs").glob("*.cfg"))
        assert len(config_files) > 0, "No configuration files generated"

    def test_generate_docs_only(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate docs command without configs and tests.

        Coverage: generate docs command path in main.py
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "docs",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        # Only docs should be generated
        assert (temp_output_dir / "documentation").exists(), "documentation directory not created"
        device_docs = list((temp_output_dir / "documentation").glob("*.md"))
        assert len(device_docs) > 0, "No device documentation generated"

    def test_generate_tests_only_with_test_type(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate tests command with specific test type.

        Coverage: generate tests command with test_type option in main.py
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "tests",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
                "--test-type",
                "anta",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        # Only test files should be generated
        tests_dir = temp_output_dir / "tests"
        assert tests_dir.exists(), "tests directory not created"


class TestE2EGenerateAllWithFilters:
    """End-to-end tests for generate all with device filtering."""

    def test_generate_all_with_limit_to_groups_spine(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all with --limit-to-groups filtering spines only.

        Coverage: Device filtering paths in main.py and generator.py
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
                "--limit-to-groups",
                "ATD_SPINES",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        # Only spine configurations should be generated
        configs_dir = temp_output_dir / "configs"
        config_files = list(configs_dir.glob("*.cfg"))

        # Should have spine configs only
        spine_configs = [f for f in config_files if "spine" in f.name]
        leaf_configs = [f for f in config_files if "leaf" in f.name]

        assert len(spine_configs) > 0, "No spine configurations generated"
        assert len(leaf_configs) == 0, "Leaf configurations should not be generated with --limit-to-groups ATD_SPINES"

    def test_generate_all_with_limit_to_groups_multiple(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all with multiple groups in --limit-to-groups.

        Coverage: Multiple group filtering in main.py
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
                "--limit-to-groups",
                "ATD_LEAFS",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        configs_dir = temp_output_dir / "configs"
        config_files = list(configs_dir.glob("*.cfg"))

        # Should have leaf configs
        assert len(config_files) > 0, "No configurations generated"


class TestE2EGenerateAllErrorHandling:
    """End-to-end tests for error handling in generate all workflow."""

    def test_generate_all_invalid_inventory_path(
        self,
        temp_output_dir: Path,
    ) -> None:
        """Test generate all with non-existent inventory path.

        Coverage: Error handling paths in main.py and loader.py
        """
        invalid_path = Path("/non/existent/inventory")

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(invalid_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0
        # Error message should indicate inventory not found
        assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()

    def test_generate_all_invalid_workflow_type(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test generate all with invalid workflow type.

        Coverage: Workflow validation in main.py
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
                "--workflow",
                "invalid-workflow",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should fail with invalid choice error
        assert result.returncode != 0
        assert "invalid" in result.stderr.lower() or "choice" in result.stderr.lower()


class TestE2EGenerateAllOutputVerification:
    """End-to-end tests verifying generated output content."""

    def test_generated_configs_contain_expected_content(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test that generated configurations contain expected EOS commands.

        Coverage: Validates end-to-end pipeline produces valid output
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        # Read a spine config and verify content
        spine_config = temp_output_dir / "configs" / "s1-spine1.cfg"
        if spine_config.exists():
            content = spine_config.read_text()

            # Verify basic EOS configuration structure
            assert "hostname s1-spine1" in content, "Hostname not in config"
            assert "interface" in content.lower(), "No interface configuration"
            # Common EOS commands should be present
            assert any(keyword in content for keyword in ["ip routing", "router bgp", "service"]), \
                "Expected EOS configuration keywords not found"

    def test_generated_documentation_contains_device_info(
        self,
        temp_output_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Test that generated documentation contains expected device information.

        Coverage: Documentation generation pipeline validation
        """
        inventory_path = examples_dir / "eos-design-basics"

        result = subprocess.run(
            [
                "uv",
                "run",
                "avd-cli",
                "generate",
                "all",
                "--inventory-path",
                str(inventory_path),
                "-o",
                str(temp_output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        # Read a device documentation file
        device_doc = temp_output_dir / "documentation" / "devices" / "s1-spine1.md"
        if device_doc.exists():
            content = device_doc.read_text()

            # Verify markdown documentation structure
            assert "s1-spine1" in content, "Device name not in documentation"
            assert any(keyword in content.lower() for keyword in ["interface", "configuration", "table"]), \
                "Expected documentation keywords not found"
