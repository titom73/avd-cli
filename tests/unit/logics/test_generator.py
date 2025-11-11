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

from avd_cli.exceptions import ConfigurationGenerationError, DocumentationGenerationError, TestGenerationError
from avd_cli.logics.generator import ConfigurationGenerator, DocumentationGenerator, TestGenerator, generate_all
from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData


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
    global_vars = {"fabric_name": "TEST_FABRIC", "design": {"type": "l3ls-evpn"}}

    group_vars = {
        "DC1": {
            "spine": {"defaults": {"platform": "7050X3"}, "nodes": [{"name": "spine01", "id": 1}]},
            "leaf": {"defaults": {"platform": "722XP"}, "node_groups": [{"nodes": [{"name": "leaf01", "id": 1}]}]},
        },
        "DC2": {"spine": {"defaults": {"platform": "7050X3"}, "nodes": [{"name": "dc2-spine01", "id": 1}]}},
    }

    host_vars = {"spine01": {"type": "spine"}, "leaf01": {"type": "leaf"}, "dc2-spine01": {"type": "spine"}}

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

    def test_generate_creates_output_directory(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_with_limit_to_groups(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test configuration generation limited to specific groups.

        Given: Inventory with 2 fabrics (DC1, DC2)
        When: Calling generate() with limit_to_groups=['DC1']
        Then: Only DC1 devices are processed
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path, limit_to_groups=["DC1"])

        # Should generate 2 configs (DC1 devices only)
        assert len(result) == 2
        # Check that only DC1 devices are generated
        hostnames = [f.stem for f in result]
        assert "spine01" in hostnames
        assert "leaf01" in hostnames
        assert "dc2-spine01" not in hostnames

    def test_generate_empty_inventory(self, tmp_path: Path) -> None:
        """Test test generation with empty inventory.

        Given: Empty inventory
        When: Calling generate()
        Then: Returns empty list (no devices to process)
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        # Create empty inventory
        empty_inventory = InventoryData(root_path=tmp_path, fabrics=[], global_vars={}, group_vars={}, host_vars={})

        result = generator.generate(empty_inventory, output_path)

        # Should return empty list (no devices = no files generated)
        assert len(result) == 0

    def test_generate_raises_on_write_error(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test error handling when file write fails.

        Given: Sample inventory
        When: File write operation fails
        Then: Raises ConfigurationGenerationError
        """
        generator = ConfigurationGenerator()
        output_path = tmp_path / "output"

        # Mock open() to raise permission error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(ConfigurationGenerationError, match="Failed to generate configurations"):
                generator.generate(sample_inventory, output_path)

    def test_generate_cli_config_workflow(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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
        mock_validation.deprecation_warnings = ["Warning 1: Old syntax", "Warning 2: Deprecated field"]
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
            "spine": {"node_groups": [{"nodes": [{"name": "spine01", "id": 1}, {"name": "spine02", "id": 2}]}]},
            "leaf": {
                "node_groups": [{"nodes": [{"name": "leaf01", "id": 1}]}, {"nodes": [{"name": "leaf02", "id": 2}]}]
            },
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

        data = {"spine": {"node_groups": [{"nodes": [{"name": "spine01", "id": 10}, {"name": "spine02", "id": 20}]}]}}

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

    def test_build_pyavd_inputs_from_inventory(self, sample_inventory: InventoryData) -> None:
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

    def test_build_pyavd_inputs_empty_devices(self, sample_inventory: InventoryData) -> None:
        """Test _build_pyavd_inputs_from_inventory with empty device list.

        Given: Empty device list
        When: Building pyavd inputs
        Then: Returns empty dictionary
        """
        generator = ConfigurationGenerator()

        result = generator._build_pyavd_inputs_from_inventory(sample_inventory, [])

        assert result == {}

    def test_convert_inventory_to_pyavd_inputs(self) -> None:
        """Test _convert_inventory_to_pyavd_inputs method (wrapper).

        Given: Inventory with devices and host variables
        When: Converting to pyavd inputs via wrapper
        Then: Returns proper input structure from inventory variables
        """
        from ipaddress import IPv4Address

        generator = ConfigurationGenerator()

        # Create device
        device = DeviceDefinition(
            hostname="test-spine",
            platform="7050X3",
            mgmt_ip=IPv4Address("192.168.1.1"),
            device_type="spine",
            fabric="TEST",
        )

        # Create inventory with host variables (simulating what InventoryLoader provides)
        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[],
            global_vars={"fabric_name": "TEST"},
            group_vars={},
            host_vars={
                "test-spine": {
                    "hostname": "test-spine",
                    "platform": "7050X3",
                    "mgmt_ip": "192.168.1.1",
                    "type": "spine",
                    "pod": "POD1",
                    "rack": "RACK1",
                    "mgmt_gateway": "192.168.1.254",
                    "serial_number": "ABC123",
                    "system_mac_address": "00:11:22:33:44:55",
                    "custom_key": "custom_value",
                    "structured_config": {"router_bgp": {"as": "65000"}},
                }
            },
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

    def test_generate_all_devices(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_all_files_content(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_creates_output_directory(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_all_devices(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_with_limit_to_groups(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test documentation generation limited to groups.

        Given: Inventory with 2 fabrics
        When: Calling generate() with limit_to_groups=['DC2']
        Then: Generates only 1 doc (DC2 devices)
        """
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path, limit_to_groups=["DC2"])

        assert len(result) == 1
        hostnames = [f.stem for f in result]
        assert "dc2-spine01" in hostnames

    def test_generate_file_content(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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
        import sys

        generator = DocumentationGenerator()
        empty_inventory = InventoryData(root_path=tmp_path, fabrics=[])

        # Remove pyavd from sys.modules to simulate import error
        pyavd_backup = sys.modules.get("pyavd")
        if "pyavd" in sys.modules:
            del sys.modules["pyavd"]

        try:
            # Mock import to raise ImportError
            with patch.dict(sys.modules, {"pyavd": None}):
                with pytest.raises(DocumentationGenerationError, match="pyavd library not installed"):
                    generator.generate(empty_inventory, tmp_path / "output")
        finally:
            # Restore pyavd if it was present
            if pyavd_backup is not None:
                sys.modules["pyavd"] = pyavd_backup

    def test_generate_raises_on_write_error(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test error handling when file write fails.

        Given: Sample inventory
        When: File write operation fails
        Then: Raises DocumentationGenerationError
        """
        generator = DocumentationGenerator()
        output_path = tmp_path / "output"

        # Mock open() to raise permission error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(DocumentationGenerationError, match="Failed to generate documentation"):
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

    def test_generate_creates_output_directory(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_creates_test_file(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test test file generation.

        Given: Sample inventory
        When: Calling generate()
        Then: Generates ANTA catalog and inventory files
        """
        generator = TestGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        # Generates two files: anta_catalog.yml and anta_inventory.yml
        assert len(result) == 2
        assert all(f.suffix == ".yaml" or f.suffix == ".yml" for f in result)
        assert all(f.exists() for f in result)

        # Check that we have both expected files
        file_names = {f.name for f in result}
        assert "anta_catalog.yml" in file_names
        assert "anta_inventory.yml" in file_names

    def test_generate_with_limit_to_groups(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test test generation limited to groups.

        Given: Inventory with 2 fabrics
        When: Calling generate() with limit_to_groups=['DC1']
        Then: Test file includes only DC1 devices
        """
        generator = TestGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path, limit_to_groups=["DC1"])

        # Should have test files
        assert len(result) > 0  # Should have files for DC1 devices

        # Check content of first test file
        test_file = result[0]
        content = test_file.read_text(encoding="utf-8")
        # Test file should contain test content
        assert len(content) > 0

    def test_generate_file_content(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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
        Then: Returns empty list (no files generated without devices)
        """
        empty_inventory = InventoryData(
            root_path=tmp_path,
            fabrics=[],
        )
        generator = TestGenerator()
        output_path = tmp_path / "output"

        result = generator.generate(empty_inventory, output_path)

        # With no devices, no files should be generated
        assert len(result) == 0

    def test_generate_raises_on_write_error(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_with_custom_test_type(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test generation with custom test type.

        Given: Custom test type 'robot'
        When: Generating tests
        Then: Generator initialized with custom type (currently generates ANTA)

        Note: pyavd.get_anta_catalog() always generates ANTA format tests.
        The test_type parameter is kept for backward compatibility but
        doesn't change the output format.
        """
        generator = TestGenerator(test_type="robot")
        output_path = tmp_path / "output"

        result = generator.generate(sample_inventory, output_path)

        # Should still generate ANTA files (pyavd only supports ANTA)
        assert len(result) == 2
        assert generator.test_type == "robot"  # Type stored but not used

        # Check that we get ANTA catalog content
        catalog_file = [f for f in result if f.name == "anta_catalog.yml"][0]
        content = catalog_file.read_text(encoding="utf-8")
        assert "ANTA" in content or "anta.tests" in content


class TestGenerateAll:
    """Test generate_all convenience function."""

    def test_generate_all_default_params(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test generate_all with default parameters.

        Given: Sample inventory and output path
        When: Calling generate_all()
        Then: Generates configs, docs, and tests
        """
        output_path = tmp_path / "output"

        configs, docs, tests = generate_all(sample_inventory, output_path)

        assert len(configs) == 3
        assert len(docs) == 3
        assert len(tests) >= 1  # At least one test file

    def test_generate_all_with_workflow(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test generate_all with custom workflow.

        Given: Custom workflow parameter
        When: Calling generate_all()
        Then: Workflow is passed to ConfigurationGenerator
        """
        output_path = tmp_path / "output"

        configs, docs, tests = generate_all(sample_inventory, output_path, workflow="config-only")

        # All outputs should still be generated
        assert len(configs) == 3
        assert len(docs) == 3
        assert len(tests) >= 1  # At least one test file

    def test_generate_all_with_limit_to_groups(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
        """Test generate_all with limit_to_groups.

        Given: limit_to_groups parameter
        When: Calling generate_all()
        Then: All generators respect the filter
        """
        output_path = tmp_path / "output"

        configs, docs, tests = generate_all(sample_inventory, output_path, limit_to_groups=["DC1"])

        # Only DC1 devices (2 devices)
        assert len(configs) == 2
        assert len(docs) == 2
        # Generates test files for DC1 devices
        assert len(tests) >= 1

    def test_generate_all_creates_all_directories(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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

    def test_generate_all_returns_all_paths(self, sample_inventory: InventoryData, tmp_path: Path) -> None:
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


class TestDeepMerge:
    """Test deep merge functionality for dual schema support.

    Bug Context
    -----------
    PyAVD has two schemas:
    - eos_designs: High-level fabric topology
    - eos_cli_config_gen: Low-level CLI configurations

    The _deep_merge method ensures both schemas are properly merged,
    with structured_config from eos_designs taking precedence over
    inputs containing eos_cli_config_gen variables.
    """

    def test_deep_merge_simple_dicts(self):
        """Test deep merge with simple non-overlapping dictionaries.

        Given: Two simple dicts with different keys
        When: Deep merging them
        Then: Result contains all keys from both dicts
        """
        gen = ConfigurationGenerator()

        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}

        result = gen._deep_merge(dict1, dict2)

        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}

    def test_deep_merge_overlapping_simple_values(self):
        """Test deep merge with overlapping simple values.

        Given: Two dicts with same keys
        When: Deep merging them
        Then: Second dict values take precedence
        """
        gen = ConfigurationGenerator()

        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 20, "c": 3}

        result = gen._deep_merge(dict1, dict2)

        assert result == {"a": 1, "b": 20, "c": 3}

    def test_deep_merge_nested_dicts(self):
        """Test deep merge with nested dictionaries.

        Given: Two dicts with nested structures
        When: Deep merging them
        Then: Nested dicts are merged recursively
        """
        gen = ConfigurationGenerator()

        dict1 = {
            "level1": {
                "level2": {
                    "a": 1,
                    "b": 2,
                }
            }
        }

        dict2 = {
            "level1": {
                "level2": {
                    "b": 20,
                    "c": 3,
                }
            }
        }

        result = gen._deep_merge(dict1, dict2)

        expected = {
            "level1": {
                "level2": {
                    "a": 1,
                    "b": 20,
                    "c": 3,
                }
            }
        }

        assert result == expected

    def test_deep_merge_lists_are_replaced(self):
        """Test that lists are replaced, not merged.

        Given: Two dicts with list values for same key
        When: Deep merging them
        Then: Second list replaces first list entirely
        """
        gen = ConfigurationGenerator()

        dict1 = {"items": [1, 2, 3]}
        dict2 = {"items": [4, 5]}

        result = gen._deep_merge(dict1, dict2)

        assert result == {"items": [4, 5]}

    def test_deep_merge_eos_cli_config_gen_with_eos_designs(self):
        """Test merge of eos_cli_config_gen and eos_designs variables.

        Bug Context
        -----------
        This simulates the actual bug fix scenario:
        - inputs contain eos_cli_config_gen vars (aliases, ntp, aaa)
        - structured_config from eos_designs contains topology (bgp, evpn)
        - Both should be present in final result
        - structured_config takes precedence for overlapping keys

        Given: inputs (eos_cli_config_gen) and structured_config (eos_designs)
        When: Deep merging them
        Then: Both types of variables are present
        """
        gen = ConfigurationGenerator()

        # Simulate eos_cli_config_gen variables from group_vars
        inputs = {
            "aliases": ["sib show ip bgp summary", "sir show ip route"],
            "ntp": {
                "local_interface": {"name": "Management1", "vrf": "MGMT"},
                "servers": [
                    {"name": "192.168.0.1", "burst": True, "iburst": True},
                ]
            },
            "router_bfd": {
                "multihop": {
                    "interval": 1200,
                    "min_rx": 1200,
                    "multiplier": 3,
                }
            },
            "aaa_authentication": {
                "login": {"default": "local"},
            },
        }

        # Simulate eos_designs output (structured_config from PyAVD)
        structured_config = {
            "router_bgp": {
                "as": 65001,
                "router_id": "10.0.0.1",
            },
            "vlan_interfaces": [
                {"name": "Vlan100", "ip_address": "10.10.10.1/24"}
            ],
            # Overlapping key that should take precedence
            "router_bfd": {
                "multihop": {
                    "interval": 1500,  # Different value from inputs
                }
            }
        }

        result = gen._deep_merge(inputs, structured_config)

        # Verify eos_cli_config_gen variables are present
        assert "aliases" in result
        assert "ntp" in result
        assert "aaa_authentication" in result

        # Verify eos_designs variables are present
        assert "router_bgp" in result
        assert "vlan_interfaces" in result

        # Verify structured_config took precedence for overlapping keys
        assert result["router_bfd"]["multihop"]["interval"] == 1500

    def test_deep_merge_preserves_none_values(self):
        """Test that None values are preserved correctly.

        Given: Dicts with None values
        When: Deep merging them
        Then: None values are not ignored
        """
        gen = ConfigurationGenerator()

        dict1 = {"a": 1, "b": None}
        dict2 = {"c": None, "d": 4}

        result = gen._deep_merge(dict1, dict2)

        assert result == {"a": 1, "b": None, "c": None, "d": 4}

    def test_deep_merge_empty_dicts(self):
        """Test merge with empty dictionaries.

        Given: One or both dicts are empty
        When: Deep merging them
        Then: Non-empty dict is returned
        """
        gen = ConfigurationGenerator()

        dict1 = {"a": 1}
        dict2 = {}

        result1 = gen._deep_merge(dict1, dict2)
        result2 = gen._deep_merge(dict2, dict1)

        assert result1 == {"a": 1}
        assert result2 == {"a": 1}

    def test_deep_merge_does_not_modify_originals(self):
        """Test that original dicts are not modified.

        Given: Two dicts
        When: Deep merging them
        Then: Original dicts remain unchanged
        """
        gen = ConfigurationGenerator()

        dict1 = {"a": 1, "nested": {"x": 10}}
        dict2 = {"b": 2, "nested": {"y": 20}}

        gen._deep_merge(dict1, dict2)

        # Verify originals are unchanged (shallow check)
        assert "b" not in dict1
        assert "a" not in dict2

        # Note: Full deep immutability would require deep copy,
        # but for our use case, top-level immutability is sufficient

    def test_deep_merge_complex_avd_scenario(self):
        """Test realistic AVD scenario with complex nested structures.

        Given: Complex AVD variable structures
        When: Deep merging them
        Then: All variables are properly merged
        """
        gen = ConfigurationGenerator()

        # Simulate complex eos_cli_config_gen from multiple group_vars
        inputs = {
            "vlans": [
                {"id": 100, "name": "campus-users"},
                {"id": 300, "name": "campus-voice"},
            ],
            "interface_profiles": [
                {
                    "profile": "CAMPUS_ACCESS",
                    "parent_profile": "TENANT",
                }
            ],
            "logging": {
                "console": "critical",
                "monitor": "disabled",
            },
            "spanning_tree": {
                "mode": "mstp",
            }
        }

        # Simulate eos_designs structured_config output
        structured_config = {
            "vlans": [
                {"id": 4094, "name": "MLAG", "trunk_groups": ["MLAG"]},
            ],
            "vlan_interfaces": [
                {"name": "Vlan4094", "ip_address": "10.255.255.1/31"}
            ],
            "spanning_tree": {
                "mode": "rstp",  # eos_designs overrides
                "priority": 4096,
            }
        }

        result = gen._deep_merge(inputs, structured_config)

        # Verify VLAN list was replaced (not merged)
        assert len(result["vlans"]) == 1
        assert result["vlans"][0]["id"] == 4094

        # Verify interface_profiles preserved
        assert "interface_profiles" in result

        # Verify logging preserved
        assert "logging" in result

        # Verify spanning_tree merged with precedence
        assert result["spanning_tree"]["mode"] == "rstp"  # From structured_config
        assert result["spanning_tree"]["priority"] == 4096
