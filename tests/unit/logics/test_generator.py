#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for configuration generation.

Tests for ConfigurationGenerator, DocumentationGenerator, TestGenerator,
and generate_all function. Validates file creation, directory handling,
and error cases.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from avd_cli.exceptions import (ConfigurationGenerationError,
                                DocumentationGenerationError,
                                TestGenerationError)
from avd_cli.logics.generator import (ConfigurationGenerator,
                                      DocumentationGenerator, TestGenerator,
                                      generate_all)
from avd_cli.models.inventory import (DeviceDefinition, FabricDefinition,
                                      InventoryData)


@pytest.fixture
def sample_inventory(tmp_path: Path) -> InventoryData:
    """Create sample inventory for testing.

    Returns
    -------
    InventoryData
        Sample inventory with 3 devices across 2 fabrics
    """
    from ipaddress import IPv4Address

    spine1 = DeviceDefinition(
        hostname="spine01",
        platform="7050X3",
        mgmt_ip=IPv4Address("192.168.1.10"),
        device_type="spine",
        fabric="DC1",
    )
    leaf1 = DeviceDefinition(
        hostname="leaf01",
        platform="722XP",
        mgmt_ip=IPv4Address("192.168.1.20"),
        device_type="leaf",
        fabric="DC1",
    )
    spine2 = DeviceDefinition(
        hostname="dc2-spine01",
        platform="7050X3",
        mgmt_ip=IPv4Address("192.168.2.10"),
        device_type="spine",
        fabric="DC2",
    )

    fabric1 = FabricDefinition(
        name="DC1",
        design_type="l3ls-evpn",
        spine_devices=[spine1],
        leaf_devices=[leaf1],
    )
    fabric2 = FabricDefinition(
        name="DC2",
        design_type="l3ls-evpn",
        spine_devices=[spine2],
    )

    # Add minimal AVD variables structure required by pyavd
    # This simulates what InventoryLoader would provide
    global_vars = {
        "fabric_name": "TEST_FABRIC",
        "design": {"type": "l3ls-evpn"}
    }

    group_vars = {
        "DC1": {
            "spine": {
                "defaults": {"platform": "7050X3"},
                "nodes": [{"name": "spine01", "id": 1}]
            },
            "leaf": {
                "defaults": {"platform": "722XP"},
                "node_groups": [{"nodes": [{"name": "leaf01", "id": 1}]}]
            }
        },
        "DC2": {
            "spine": {
                "defaults": {"platform": "7050X3"},
                "nodes": [{"name": "dc2-spine01", "id": 1}]
            }
        }
    }

    host_vars = {
        "spine01": {"type": "spine"},
        "leaf01": {"type": "leaf"},
        "dc2-spine01": {"type": "spine"}
    }

    return InventoryData(
        root_path=tmp_path,
        fabrics=[fabric1, fabric2],
        global_vars=global_vars,
        group_vars=group_vars,
        host_vars=host_vars,
    )


class TestConfigurationGenerator:
    """Test ConfigurationGenerator class."""

    def test_init_default_workflow(self) -> None:
        """Test generator initialization with default workflow.

        Given: No workflow specified
        When: Creating ConfigurationGenerator
        Then: Workflow is set to 'eos-design'
        """
        generator = ConfigurationGenerator()
        assert generator.workflow == "eos-design"

    def test_init_custom_workflow(self) -> None:
        """Test generator initialization with custom workflow.

        Given: Custom workflow 'cli-config'
        When: Creating ConfigurationGenerator
        Then: Workflow is set correctly
        """
        generator = ConfigurationGenerator(workflow="cli-config")
        assert generator.workflow == "cli-config"

    def test_init_legacy_workflow_full(self) -> None:
        """Test generator initialization with legacy 'full' workflow.

        Given: Legacy workflow 'full'
        When: Creating ConfigurationGenerator
        Then: Workflow is normalized to 'eos-design'
        """
        generator = ConfigurationGenerator(workflow="full")
        assert generator.workflow == "eos-design"

    def test_init_legacy_workflow_config_only(self) -> None:
        """Test generator initialization with legacy 'config-only' workflow.

        Given: Legacy workflow 'config-only'
        When: Creating ConfigurationGenerator
        Then: Workflow is normalized to 'cli-config'
        """
        generator = ConfigurationGenerator(workflow="config-only")
        assert generator.workflow == "cli-config"

    def test_generate_creates_output_directory(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test configuration generation creates output directory.

        Given: Sample inventory and output path
        When: Calling generate()
        Then: configurations/ directory is created
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        generator.generate(sample_inventory, output_path)

        configs_dir = output_path / "configs"
        assert configs_dir.exists()
        assert configs_dir.is_dir()

    def test_generate_with_limit_to_groups(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test configuration generation limited to specific groups.

        Given: Inventory with 2 fabrics (DC1, DC2)
        When: Calling generate() with limit_to_groups=['DC1']
        Then: Only DC1 devices are processed
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(
            sample_inventory, output_path, limit_to_groups=["DC1"]
        )

        # Should generate 2 configs (DC1 devices only)
        assert len(result) == 2
        # Check that only DC1 devices are generated
        hostnames = [f.stem for f in result]
        assert "spine01" in hostnames
        assert "leaf01" in hostnames
        assert "dc2-spine01" not in hostnames

    def test_generate_empty_inventory(self, tmp_path: Path) -> None:
        """Test generation with empty inventory.

        Given: Inventory with no devices
        When: Calling generate()
        Then: Returns empty list
        """
        empty_inventory = InventoryData(
            root_path=tmp_path,
            fabrics=[],
        )
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(empty_inventory, output_path)

        assert len(result) == 0

    def test_generate_raises_on_write_error(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test error handling when file write fails.

        Given: Sample inventory
        When: File write operation fails
        Then: Raises ConfigurationGenerationError
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        # Mock open() to raise permission error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(
                ConfigurationGenerationError, match="Failed to generate configurations"
            ):
                generator.generate(sample_inventory, output_path)

    def test_generate_cli_config_workflow(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test configuration generation with cli-config workflow.

        Given: cli-config workflow
        When: Generating configurations
        Then: Skips eos_design validation
        """
        generator = ConfigurationGenerator(workflow="cli-config")
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        assert len(result) == 3
        assert all(f.exists() for f in result)

    def test_generate_with_validation_failure(
        self, sample_inventory: InventoryData, tmp_path: Path, mock_pyavd
    ) -> None:
        """Test handling of input validation failure.

        Given: pyavd validation fails
        When: Generating configurations with eos-design workflow
        Then: Raises ConfigurationGenerationError
        """
        from unittest.mock import MagicMock

        # Configure mock to return failed validation
        mock_validation = MagicMock()
        mock_validation.failed = True
        mock_validation.validation_errors = ["Error 1: Invalid input", "Error 2: Missing field"]
        mock_pyavd.validate_inputs.return_value = mock_validation

        generator = ConfigurationGenerator(workflow="eos-design")
        output_path = tmp_path / "output"

        with pytest.raises(ConfigurationGenerationError, match="Input validation failed"):
            generator.generate(sample_inventory, output_path)

    def test_generate_with_structured_config_validation_failure(
        self, sample_inventory: InventoryData, tmp_path: Path, mock_pyavd
    ) -> None:
        """Test handling of structured config validation failure.

        Given: pyavd structured config validation fails
        When: Generating configurations
        Then: Raises ConfigurationGenerationError
        """
        from unittest.mock import MagicMock

        # Input validation succeeds
        mock_input_validation = MagicMock()
        mock_input_validation.failed = False
        mock_input_validation.deprecation_warnings = []
        mock_pyavd.validate_inputs.return_value = mock_input_validation

        # Structured config validation fails
        mock_structured_validation = MagicMock()
        mock_structured_validation.failed = True
        mock_structured_validation.validation_errors = ["Structured config error"]
        mock_pyavd.validate_structured_config.return_value = mock_structured_validation

        generator = ConfigurationGenerator(workflow="eos-design")
        output_path = tmp_path / "output"

        with pytest.raises(ConfigurationGenerationError, match="Structured config validation failed"):
            generator.generate(sample_inventory, output_path)

    def test_generate_with_deprecation_warnings(
        self, sample_inventory: InventoryData, tmp_path: Path, mock_pyavd
    ) -> None:
        """Test handling of deprecation warnings.

        Given: pyavd returns deprecation warnings
        When: Generating configurations with eos-design workflow
        Then: Logs warnings but continues generation
        """
        from unittest.mock import MagicMock

        # Configure mock to return warnings
        mock_validation = MagicMock()
        mock_validation.failed = False
        mock_validation.deprecation_warnings = [
            "Warning 1: Old syntax",
            "Warning 2: Deprecated field"
        ]
        mock_pyavd.validate_inputs.return_value = mock_validation

        # Structured config validation succeeds
        mock_structured_validation = MagicMock()
        mock_structured_validation.failed = False
        mock_pyavd.validate_structured_config.return_value = mock_structured_validation

        generator = ConfigurationGenerator(workflow="eos-design")
        output_path = tmp_path / "output"

        # Should complete successfully despite warnings
        result = generator.generate(sample_inventory, output_path)
        assert len(result) == 3

    def test_convert_numeric_strings(self) -> None:
        """Test _convert_numeric_strings method.

        Given: Data with string numbers
        When: Converting numeric strings
        Then: Returns data with proper number types
        """
        generator = ConfigurationGenerator()

        # Test dict with numeric strings
        data = {"port": "9214", "vlan": "100", "name": "test", "mtu": "1500"}
        result = generator._convert_numeric_strings(data)
        assert result["port"] == 9214
        assert result["vlan"] == 100
        assert result["name"] == "test"
        assert result["mtu"] == 1500

        # Test list with numeric strings
        data_list = ["100", "200", "test", "300"]
        result_list = generator._convert_numeric_strings(data_list)
        assert result_list == [100, 200, "test", 300]

        # Test nested structure
        nested = {"outer": {"inner": "42", "values": ["1", "2", "3"]}}
        result_nested = generator._convert_numeric_strings(nested)
        assert result_nested["outer"]["inner"] == 42
        assert result_nested["outer"]["values"] == [1, 2, 3]

        # Test negative numbers
        negative_data = {"temp": "-10", "offset": "-5"}
        result_negative = generator._convert_numeric_strings(negative_data)
        assert result_negative["temp"] == -10
        assert result_negative["offset"] == -5

        # Test floats
        float_data = {"rate": "1.5", "threshold": "0.95"}
        result_float = generator._convert_numeric_strings(float_data)
        assert result_float["rate"] == 1.5
        assert result_float["threshold"] == 0.95

    def test_deep_merge(self) -> None:
        """Test _deep_merge method.

        Given: Two dictionaries
        When: Deep merging them
        Then: Returns properly merged dictionary
        """
        generator = ConfigurationGenerator()

        base = {"a": 1, "b": {"c": 2, "d": 3}, "e": 5}
        update = {"b": {"c": 20, "f": 4}, "g": 6}

        result = generator._deep_merge(base, update)

        assert result["a"] == 1
        assert result["b"]["c"] == 20  # Updated
        assert result["b"]["d"] == 3  # Preserved
        assert result["b"]["f"] == 4  # Added
        assert result["e"] == 5
        assert result["g"] == 6

    def test_determine_device_type(self) -> None:
        """Test _determine_device_type method.

        Given: AVD topology structure with devices
        When: Determining device type by hostname
        Then: Returns correct device type
        """
        generator = ConfigurationGenerator()

        data = {
            "spine": {
                "node_groups": [
                    {"nodes": [{"name": "spine01", "id": 1}, {"name": "spine02", "id": 2}]}
                ]
            },
            "leaf": {
                "node_groups": [
                    {"nodes": [{"name": "leaf01", "id": 1}]},
                    {"nodes": [{"name": "leaf02", "id": 2}]}
                ]
            }
        }

        assert generator._determine_device_type(data, "spine01") == "spine"
        assert generator._determine_device_type(data, "spine02") == "spine"
        assert generator._determine_device_type(data, "leaf01") == "leaf"
        assert generator._determine_device_type(data, "leaf02") == "leaf"
        assert generator._determine_device_type(data, "unknown") is None

    def test_determine_device_type_invalid_structure(self) -> None:
        """Test _determine_device_type with invalid data structures.

        Given: Invalid or incomplete topology structures
        When: Determining device type
        Then: Returns None without crashing
        """
        generator = ConfigurationGenerator()

        # Missing node_groups
        data = {"spine": {}}
        assert generator._determine_device_type(data, "spine01") is None

        # node_groups not a list
        data = {"spine": {"node_groups": "invalid"}}
        assert generator._determine_device_type(data, "spine01") is None

        # nodes not a list
        data = {"spine": {"node_groups": [{"nodes": "invalid"}]}}
        assert generator._determine_device_type(data, "spine01") is None

        # Empty structures
        data = {"spine": {"node_groups": []}}
        assert generator._determine_device_type(data, "spine01") is None

    def test_extract_node_id(self) -> None:
        """Test _extract_node_id method.

        Given: AVD topology structure with node IDs
        When: Extracting node ID by hostname
        Then: Returns correct node ID
        """
        generator = ConfigurationGenerator()

        data = {
            "spine": {
                "node_groups": [
                    {"nodes": [{"name": "spine01", "id": 10}, {"name": "spine02", "id": 20}]}
                ]
            }
        }

        assert generator._extract_node_id(data, "spine01") == 10
        assert generator._extract_node_id(data, "spine02") == 20
        assert generator._extract_node_id(data, "unknown") is None

    def test_extract_node_id_invalid_types(self) -> None:
        """Test _extract_node_id with invalid ID types.

        Given: Node with invalid ID type
        When: Extracting node ID
        Then: Returns None and logs warning
        """
        generator = ConfigurationGenerator()

        # String ID that can be converted
        data = {"spine": {"node_groups": [{"nodes": [{"name": "spine01", "id": "10"}]}]}}
        assert generator._extract_node_id(data, "spine01") == 10

        # Invalid ID type
        data = {"spine": {"node_groups": [{"nodes": [{"name": "spine01", "id": "invalid"}]}]}}
        assert generator._extract_node_id(data, "spine01") is None

    def test_build_pyavd_inputs_from_inventory(
        self, sample_inventory: InventoryData
    ) -> None:
        """Test _build_pyavd_inputs_from_inventory method.

        Given: Inventory with devices and variables
        When: Building pyavd inputs
        Then: Returns correct input structure per device
        """
        generator = ConfigurationGenerator()
        devices = sample_inventory.get_all_devices()

        result = generator._build_pyavd_inputs_from_inventory(sample_inventory, devices)

        # Should have entry for each device
        assert len(result) == 3
        assert "spine01" in result
        assert "leaf01" in result
        assert "dc2-spine01" in result

        # Each device should have hostname and type
        for hostname, inputs in result.items():
            assert inputs["hostname"] == hostname
            assert "type" in inputs

    def test_build_pyavd_inputs_empty_devices(
        self, sample_inventory: InventoryData
    ) -> None:
        """Test _build_pyavd_inputs_from_inventory with empty device list.

        Given: Empty device list
        When: Building pyavd inputs
        Then: Returns empty dictionary
        """
        generator = ConfigurationGenerator()

        result = generator._build_pyavd_inputs_from_inventory(sample_inventory, [])

        assert result == {}

    def test_convert_inventory_to_pyavd_inputs(self) -> None:
        """Test _convert_inventory_to_pyavd_inputs method.

        Given: Inventory with devices having custom variables
        When: Converting to pyavd inputs
        Then: Returns proper input structure
        """
        from ipaddress import IPv4Address

        generator = ConfigurationGenerator()

        # Create device with custom variables
        device = DeviceDefinition(
            hostname="test-spine",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.1"),
            device_type="spine",
            fabric="TEST",
            pod="POD1",
            rack="RACK1",
            mgmt_gateway=IPv4Address("192.168.1.254"),
            serial_number="ABC123",
            system_mac_address="00:11:22:33:44:55",
            custom_variables={"custom_key": "custom_value"},
            structured_config={"router_bgp": {"as": "65000"}}
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[]
        )

        result = generator._convert_inventory_to_pyavd_inputs(inventory, [device])

        assert "test-spine" in result
        device_vars = result["test-spine"]
        assert device_vars["hostname"] == "test-spine"
        assert device_vars["platform"] == "7050X3"
        assert device_vars["mgmt_ip"] == "192.168.1.1"
        assert device_vars["type"] == "spine"
        assert device_vars["fabric_name"] == "TEST"
        assert device_vars["pod"] == "POD1"
        assert device_vars["rack"] == "RACK1"
        assert device_vars["mgmt_gateway"] == "192.168.1.254"
        assert device_vars["serial_number"] == "ABC123"
        assert device_vars["system_mac_address"] == "00:11:22:33:44:55"
        assert device_vars["custom_key"] == "custom_value"
        assert "structured_config" in device_vars

    def test_generate_all_devices(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test configuration generation for all devices.

        Given: Inventory with 3 devices
        When: Calling generate() without filters
        Then: Generates 3 configuration files
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        assert len(result) == 3
        assert all(f.suffix == ".cfg" for f in result)
        assert all(f.exists() for f in result)

        # Check filenames
        hostnames = [f.stem for f in result]
        assert "spine01" in hostnames
        assert "leaf01" in hostnames
        assert "dc2-spine01" in hostnames

    def test_generate_all_files_content(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test content of generated configuration files.

        Given: Sample inventory
        When: Generating configurations
        Then: Files contain device-specific content
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        # Check each config file has hostname in content
        for config_file in result:
            content = config_file.read_text(encoding="utf-8")
            hostname = config_file.stem
            assert hostname in content
            assert "Configuration for" in content or "hostname" in content


class TestDocumentationGenerator:
    """Test DocumentationGenerator class."""

    def test_init(self) -> None:
        """Test documentation generator initialization.

        Given: No parameters
        When: Creating DocumentationGenerator
        Then: Generator is initialized
        """
        generator = DocumentationGenerator()
        assert generator.logger is not None

    def test_generate_creates_output_directory(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test documentation generation creates output directory.

        Given: Sample inventory and output path
        When: Calling generate()
        Then: documentation/ directory is created
        """
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        generator.generate(sample_inventory, output_path)

        docs_dir = output_path / "documentation"
        assert docs_dir.exists()
        assert docs_dir.is_dir()

    def test_generate_all_devices(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test documentation generation for all devices.

        Given: Inventory with 3 devices
        When: Calling generate() without filters
        Then: Generates 3 documentation files
        """
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        assert len(result) == 3
        assert all(f.suffix == ".md" for f in result)
        assert all(f.exists() for f in result)

    def test_generate_with_limit_to_groups(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test documentation generation limited to groups.

        Given: Inventory with 2 fabrics
        When: Calling generate() with limit_to_groups=['DC2']
        Then: Generates only 1 doc (DC2 devices)
        """
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(
            sample_inventory, output_path, limit_to_groups=["DC2"]
        )

        assert len(result) == 1
        hostnames = [f.stem for f in result]
        assert "dc2-spine01" in hostnames

    def test_generate_file_content(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test content of generated documentation files.

        Given: Sample inventory
        When: Generating documentation
        Then: Files contain device information in markdown
        """
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        # Check first doc file content
        doc_file = result[0]
        content = doc_file.read_text(encoding="utf-8")

        assert "# " in content  # Markdown heading
        assert "**Platform:**" in content
        assert "**Type:**" in content
        assert "**Management IP:**" in content
        assert "Generated by avd-cli" in content

    def test_generate_empty_inventory(self, tmp_path: Path) -> None:
        """Test generation with empty inventory.

        Given: Inventory with no devices
        When: Calling generate()
        Then: Returns empty list
        """
        empty_inventory = InventoryData(
            root_path=tmp_path,
            fabrics=[],
        )
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(empty_inventory, output_path)

        assert len(result) == 0

    def test_generate_raises_on_import_error(self, tmp_path: Path) -> None:
        """Test error when pyavd is not available.

        Given: pyavd not importable
        When: Calling generate()
        Then: Raises DocumentationGenerationError with helpful message
        """
        generator = DocumentationGenerator()
        empty_inventory = InventoryData(root_path=tmp_path, fabrics=[])

        # Mock the _import_pyavd method to raise DocumentationGenerationError
        with patch.object(
            generator,
            '_import_pyavd',
            side_effect=DocumentationGenerationError(
                "pyavd library not installed. Install with: pip install pyavd"
            )
        ):
            with pytest.raises(DocumentationGenerationError, match="pyavd library not installed"):
                generator.generate(empty_inventory, tmp_path / "output")

    def test_generate_raises_on_write_error(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test error handling when file write fails.

        Given: Sample inventory
        When: File write operation fails
        Then: Raises DocumentationGenerationError
        """
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        # Mock open() to raise permission error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(
                DocumentationGenerationError, match="Failed to generate documentation"
            ):
                generator.generate(sample_inventory, output_path)


class TestTestGenerator:
    """Test TestGenerator class."""

    def test_init_default_test_type(self) -> None:
        """Test generator initialization with default test type.

        Given: No test type specified
        When: Creating TestGenerator
        Then: Test type is set to 'anta'
        """
        generator = TestGenerator()
        assert generator.test_type == "anta"

    def test_init_custom_test_type(self) -> None:
        """Test generator initialization with custom test type.

        Given: Custom test type 'robot'
        When: Creating TestGenerator
        Then: Test type is set correctly
        """
        generator = TestGenerator(test_type="robot")
        assert generator.test_type == "robot"

    def test_generate_creates_output_directory(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test test generation creates output directory.

        Given: Sample inventory and output path
        When: Calling generate()
        Then: tests/ directory is created
        """
        generator = TestGenerator()
        output_path = tmp_path / "output"

        generator.generate(sample_inventory, output_path)

        tests_dir = output_path / "tests"
        assert tests_dir.exists()
        assert tests_dir.is_dir()

    def test_generate_creates_test_file(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test test file generation.

        Given: Sample inventory
        When: Calling generate()
        Then: Generates YAML test file
        """
        generator = TestGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        # Now generates one file per device
        assert len(result) > 1  # Multiple devices = multiple files
        assert all(f.suffix == ".yaml" for f in result)
        assert all("_tests.yaml" in f.name for f in result)
        assert all(f.exists() for f in result)

    def test_generate_with_limit_to_groups(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test test generation limited to groups.

        Given: Inventory with 2 fabrics
        When: Calling generate() with limit_to_groups=['DC1']
        Then: Test file includes only DC1 devices
        """
        generator = TestGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(
            sample_inventory, output_path, limit_to_groups=["DC1"]
        )

        # Read test files and check content
        # Now we have individual device files, check that DC1 devices are present
        device_files = [f for f in result if "DC1" in str(f) or "spine01" in f.name or "leaf01" in f.name]
        assert len(device_files) > 0  # Should have files for DC1 devices

        # Check content of first device file
        test_file = result[0]
        content = test_file.read_text(encoding="utf-8")
        # Individual device tests use 8.8.8.8 for connectivity, not peer IPs
        assert "8.8.8.8" in content  # Internet connectivity test

    def test_generate_file_content(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test content of generated test file.

        Given: Sample inventory
        When: Generating tests
        Then: File contains ANTA test structure
        """
        generator = TestGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        test_file = result[0]
        content = test_file.read_text(encoding="utf-8")

        # Check for ANTA catalog structure
        assert "anta.tests" in content  # ANTA test namespace
        assert "VerifyReachability" in content or "connectivity" in content.lower()
        # Note: ANTA catalog uses different YAML structure than simple tests

    def test_generate_empty_inventory(self, tmp_path: Path) -> None:
        """Test generation with empty inventory.

        Given: Inventory with no devices
        When: Calling generate()
        Then: Still creates test file structure
        """
        empty_inventory = InventoryData(
            root_path=tmp_path,
            fabrics=[],
        )
        generator = TestGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(empty_inventory, output_path)

        assert len(result) == 1
        assert result[0].exists()

    def test_generate_raises_on_write_error(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test error handling when file write fails.

        Given: Sample inventory
        When: File write operation fails
        Then: Raises TestGenerationError
        """
        generator = TestGenerator()
        output_path = tmp_path / "output"

        # Mock open() to raise permission error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(TestGenerationError, match="Failed to generate tests"):
                generator.generate(sample_inventory, output_path)

    def test_generate_with_custom_test_type(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test generation with custom test type.

        Given: Custom test type 'robot'
        When: Generating tests
        Then: Test file reflects the test type
        """
        generator = TestGenerator(test_type="robot")
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        # Check test file content includes ROBOT
        test_file = result[0]
        content = test_file.read_text(encoding="utf-8")
        assert "ROBOT" in content


class TestGenerateAll:
    """Test generate_all convenience function."""

    def test_generate_all_default_params(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test generate_all with default parameters.

        Given: Sample inventory and output path
        When: Calling generate_all()
        Then: Generates configs, docs, and tests
        """
        output_path = tmp_path / "output"

        configs, docs, tests = generate_all(sample_inventory, output_path)

        assert len(configs) == 3
        assert len(docs) == 3
        assert len(tests) == 3  # Now one test file per device

    def test_generate_all_with_workflow(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test generate_all with custom workflow.

        Given: Custom workflow parameter
        When: Calling generate_all()
        Then: Workflow is passed to ConfigurationGenerator
        """
        output_path = tmp_path / "output"

        configs, docs, tests = generate_all(
            sample_inventory, output_path, workflow="config-only"
        )

        # All outputs should still be generated
        assert len(configs) == 3
        assert len(docs) == 3
        assert len(tests) == 3  # Now one test file per device

    def test_generate_all_with_limit_to_groups(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test generate_all with limit_to_groups.

        Given: limit_to_groups parameter
        When: Calling generate_all()
        Then: All generators respect the filter
        """
        output_path = tmp_path / "output"

        configs, docs, tests = generate_all(
            sample_inventory, output_path, limit_to_groups=["DC1"]
        )

        # Only DC1 devices (2 devices)
        assert len(configs) == 2
        assert len(docs) == 2
        # Now generates one test file per device, so 2 files for DC1
        assert len(tests) == 2

    def test_generate_all_creates_all_directories(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test generate_all creates all output directories.

        Given: Sample inventory
        When: Calling generate_all()
        Then: configurations/, documentation/, tests/ directories exist
        """
        output_path = tmp_path / "output"

        generate_all(sample_inventory, output_path)

        assert (output_path / "configs").exists()
        assert (output_path / "documentation").exists()
        assert (output_path / "tests").exists()

    def test_generate_all_returns_all_paths(
        self, sample_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test generate_all returns all generated file paths.

        Given: Sample inventory
        When: Calling generate_all()
        Then: Returns tuple of (configs, docs, tests) paths
        """
        output_path = tmp_path / "output"

        result = generate_all(sample_inventory, output_path)

        assert isinstance(result, tuple)
        assert len(result) == 3
        configs, docs, tests = result

        # Verify all are lists of Paths
        assert isinstance(configs, list)
        assert isinstance(docs, list)
        assert isinstance(tests, list)
        assert all(isinstance(p, Path) for p in configs)
        assert all(isinstance(p, Path) for p in docs)
        assert all(isinstance(p, Path) for p in tests)
