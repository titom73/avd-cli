#!/usr/bin/env python
# coding: utf-8 -*-

"""Configuration generation functionality.

This module provides functionality to generate device configurations,
documentation, and test files from AVD inventory data.
"""

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

from avd_cli.constants import (DEFAULT_CONFIGS_DIR, DEFAULT_DOCS_DIR,
                               DEFAULT_TESTS_DIR)
from avd_cli.exceptions import (ConfigurationGenerationError,
                                DocumentationGenerationError,
                                TestGenerationError)
from avd_cli.models.inventory import DeviceDefinition, InventoryData

logger = logging.getLogger(__name__)
console = Console()


class ConfigurationGenerator:
    """Generator for device configurations.

    This class handles generation of device configurations from AVD inventory
    data using py-avd library.

    Examples
    --------
    >>> generator = ConfigurationGenerator()
    >>> configs = generator.generate(inventory, output_path)
    >>> print(f"Generated {len(configs)} configurations")
    """

    def __init__(self, workflow: str = "eos-design") -> None:
        """Initialize the configuration generator.

        Parameters
        ----------
        workflow : str, optional
            Workflow type ('eos-design' or 'cli-config'), by default "eos-design"
            Legacy values 'full' and 'config-only' are also supported for backward compatibility.
        """
        from avd_cli.constants import normalize_workflow

        self.workflow = normalize_workflow(workflow)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate(  # noqa: C901
        self, inventory: InventoryData, output_path: Path, limit_to_groups: Optional[List[str]] = None
    ) -> List[Path]:
        """Generate device configurations.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data
        output_path : Path
            Output directory for generated configs
        limit_to_groups : Optional[List[str]], optional
            Groups to limit generation to, by default None

        Returns
        -------
        List[Path]
            List of generated configuration file paths

        Raises
        ------
        ConfigurationGenerationError
            If generation fails
        """
        self.logger.info("Generating configurations with workflow: %s", self.workflow)

        # Import pyavd
        try:
            import pyavd
        except ImportError as e:
            raise ConfigurationGenerationError(
                "pyavd library not installed. Install with: pip install pyavd"
            ) from e

        # Create output directory
        configs_dir = output_path / DEFAULT_CONFIGS_DIR
        configs_dir.mkdir(parents=True, exist_ok=True)

        generated_files: List[Path] = []

        try:
            devices = inventory.get_all_devices()

            # Filter by groups if specified
            if limit_to_groups:
                devices = [d for d in devices if d.fabric in limit_to_groups]
                self.logger.info("Limited to %d devices in groups: %s", len(devices), limit_to_groups)

            # Build pyavd inputs from inventory (already resolved by InventoryLoader)
            # This reuses the Jinja2 template resolution from InventoryLoader
            self.logger.info("Building pyavd inputs from resolved inventory")
            all_inputs = self._build_pyavd_inputs_from_inventory(inventory, devices)

            if not all_inputs:
                self.logger.warning("No devices to process")
                return generated_files

            # Step 1: Validate inputs (eos_designs schema)
            if self.workflow == "eos-design":
                self.logger.info("Validating inputs against eos_designs schema")
                for hostname, inputs in all_inputs.items():
                    validation_result = pyavd.validate_inputs(inputs)
                    if validation_result.failed:
                        errors = "\n".join(str(e) for e in validation_result.validation_errors)
                        raise ConfigurationGenerationError(
                            f"Input validation failed for {hostname}:\n{errors}"
                        )
                    if validation_result.deprecation_warnings:
                        for warning in validation_result.deprecation_warnings:
                            self.logger.warning("Deprecation warning for %s: %s", hostname, warning)

                # Step 2: Generate AVD facts (eos_design workflow)
                self.logger.info("Generating AVD facts for %d devices", len(all_inputs))
                avd_facts = pyavd.get_avd_facts(all_inputs)

                # Step 3: Generate structured configs for each device
                self.logger.info("Generating structured configurations")
                structured_configs: Dict[str, Dict[str, Any]] = {}
                for hostname, inputs in all_inputs.items():
                    structured_config = pyavd.get_device_structured_config(
                        hostname=hostname, inputs=inputs, avd_facts=avd_facts
                    )
                    structured_configs[hostname] = structured_config

            else:  # workflow == "cli-config"
                # Skip eos_design, only use eos_cli_config_gen
                self.logger.info("Using cli-config workflow (eos_cli_config_gen only)")
                structured_configs = {}
                for hostname, inputs in all_inputs.items():
                    # For cli-config, inputs should already be structured_config
                    structured_configs[hostname] = inputs

            # Step 4: Validate structured configs
            self.logger.info("Validating structured configurations")
            for hostname, structured_config in structured_configs.items():
                validation_result = pyavd.validate_structured_config(structured_config)
                if validation_result.failed:
                    errors = "\n".join(str(e) for e in validation_result.validation_errors)
                    raise ConfigurationGenerationError(
                        f"Structured config validation failed for {hostname}:\n{errors}"
                    )

            # Step 5: Generate EOS CLI configurations
            self.logger.info("Generating EOS CLI configurations")
            for hostname, structured_config in structured_configs.items():
                config_file = configs_dir / f"{hostname}.cfg"
                config_text = pyavd.get_device_config(structured_config)

                with open(config_file, "w", encoding="utf-8") as f:
                    f.write(config_text)

                generated_files.append(config_file)
                self.logger.debug("Generated config: %s", config_file)

            self.logger.info("Generated %d configuration files", len(generated_files))
            return generated_files

        except ConfigurationGenerationError:
            raise
        except Exception as e:
            raise ConfigurationGenerationError(f"Failed to generate configurations: {e}") from e

    def _convert_numeric_strings(self, data: Any) -> Any:
        """Recursively convert string representations of numbers to actual numbers.

        This handles cases where Jinja2 templates resolve to string numbers
        (e.g., "9214" → 9214) which pyavd schema expects as integers.

        Parameters
        ----------
        data : Any
            Data structure to process

        Returns
        -------
        Any
            Data with numeric strings converted to numbers
        """
        if isinstance(data, dict):
            return {key: self._convert_numeric_strings(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_numeric_strings(item) for item in data]
        elif isinstance(data, str):
            # Try to convert to int
            if data.isdigit() or (data.startswith("-") and data[1:].isdigit()):
                return int(data)
            # Try to convert to float
            try:
                if "." in data:
                    return float(data)
            except ValueError:
                pass
            return data
        else:
            return data

    def _build_pyavd_inputs_from_inventory(
        self, inventory: InventoryData, devices: List[DeviceDefinition]
    ) -> Dict[str, Dict[str, Any]]:
        """Build pyavd inputs from resolved inventory data.

        Following Ansible's model, each device gets the complete inventory structure
        (global_vars + all group_vars + host_vars) so pyavd can extract device-specific
        data from topology structures like l2leaf.node_groups[].nodes[].

        Parameters
        ----------
        inventory : InventoryData
            Complete inventory data with resolved variables
        devices : List[DeviceDefinition]
            List of devices to build inputs for

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping hostnames to their complete AVD variables
        """
        # Build the base structure: global_vars + all group_vars merged
        # This gives us the complete topology (l2leaf, l3leaf, spine structures, etc.)
        base_structure: Dict[str, Any] = deepcopy(inventory.global_vars)

        for group_name in sorted(inventory.group_vars.keys()):
            base_structure = self._deep_merge(base_structure, inventory.group_vars[group_name])

        # Convert numeric strings (from Jinja2) to proper numbers
        base_structure = self._convert_numeric_strings(base_structure)

        # Each device gets the SAME base structure + its own host_vars
        all_inputs: Dict[str, Dict[str, Any]] = {}

        # Remove 'type' from base_structure (it will be set per-device)
        base_structure.pop("type", None)

        for device in devices:
            device_input = deepcopy(base_structure)

            # Set hostname (required by pyavd)
            device_input["hostname"] = device.hostname

            # For cli-config workflow, use device.device_type directly (already in device definition)
            # For eos-design workflow, determine type from topology structure
            if self.workflow == "cli-config":
                device_input["type"] = device.device_type
                self.logger.debug(
                    "Using device type '%s' for %s (from device definition)", device.device_type, device.hostname
                )
            else:
                # Determine device type by finding which topology structure contains this device
                device_type = self._determine_device_type(base_structure, device.hostname)
                if device_type:
                    device_input["type"] = device_type
                    self.logger.debug("Determined type '%s' for device %s", device_type, device.hostname)
                else:
                    self.logger.warning("Could not determine type for device %s", device.hostname)

            # Merge host-specific variables last (they override everything)
            if device.hostname in inventory.host_vars:
                device_input = self._deep_merge(device_input, inventory.host_vars[device.hostname])

            all_inputs[device.hostname] = device_input

            self.logger.debug(
                "Built input for %s with %d top-level keys",
                device.hostname,
                len(device_input)
            )

        return all_inputs

    def _determine_device_type(self, data: Dict[str, Any], hostname: str) -> Optional[str]:  # noqa: C901
        """Determine device type by finding which topology structure contains this device.

        AVD topology types: l2leaf, l3leaf, l3spine, spine, super_spine, etc.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing topology structures
        hostname : str
            Hostname to find

        Returns
        -------
        str | None
            Device type if found, None otherwise
        """
        # Common AVD topology keys
        topology_keys = ["l2leaf", "l3leaf", "l3spine", "spine", "super_spine", "leaf"]

        for topology_key in topology_keys:
            if topology_key not in data:
                continue

            topology_data = data[topology_key]
            if not isinstance(topology_data, dict):
                continue

            node_groups = topology_data.get("node_groups", [])
            if not isinstance(node_groups, list):
                continue

            # Search through all node groups for matching hostname
            for node_group in node_groups:
                if not isinstance(node_group, dict):
                    continue

                nodes = node_group.get("nodes", [])
                if not isinstance(nodes, list):
                    continue

                for node in nodes:
                    if not isinstance(node, dict):
                        continue

                    if node.get("name") == hostname:
                        return topology_key

        return None

    def _extract_node_id(self, device_vars: Dict[str, Any], hostname: str) -> Optional[int]:  # noqa: C901
        """Extract node ID from AVD topology structure.

        AVD stores node IDs in structures like:
        - l2leaf.node_groups[].nodes[]
        - l3spine.node_groups[].nodes[]
        - spine.node_groups[].nodes[]
        - leaf.node_groups[].nodes[]

        Parameters
        ----------
        device_vars : Dict[str, Any]
            Device variables containing AVD topology structure
        hostname : str
            Hostname to find ID for

        Returns
        -------
        int | None
            Node ID if found, None otherwise
        """
        # Look for common AVD topology keys
        topology_keys = ["l2leaf", "l3spine", "spine", "leaf", "super_spine"]

        for topology_key in topology_keys:
            if topology_key not in device_vars:
                continue

            topology_data = device_vars[topology_key]
            if not isinstance(topology_data, dict):
                continue

            node_groups = topology_data.get("node_groups", [])
            if not isinstance(node_groups, list):
                continue

            # Search through all node groups for matching hostname
            for node_group in node_groups:
                if not isinstance(node_group, dict):
                    continue

                nodes = node_group.get("nodes", [])
                if not isinstance(nodes, list):
                    continue

                for node in nodes:
                    if not isinstance(node, dict):
                        continue

                    if node.get("name") == hostname:
                        node_id = node.get("id")
                        if node_id is not None:
                            # Ensure it's an integer
                            try:
                                return int(node_id)
                            except (ValueError, TypeError):
                                self.logger.warning(
                                    "Invalid node ID '%s' for device %s", node_id, hostname
                                )
                                return None

        return None

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, update takes precedence.

        Parameters
        ----------
        base : Dict[str, Any]
            Base dictionary
        update : Dict[str, Any]
            Dictionary to merge into base

        Returns
        -------
        Dict[str, Any]
            Merged dictionary
        """
        result = deepcopy(base)

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)

        return result

    def _convert_inventory_to_pyavd_inputs(
        self, inventory: InventoryData, devices: List[DeviceDefinition]
    ) -> Dict[str, Dict[str, Any]]:
        """Convert avd-cli inventory to pyavd input format.

        Parameters
        ----------
        inventory : InventoryData
            Complete inventory data
        devices : List[DeviceDefinition]
            List of devices to convert

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping hostnames to their pyavd input variables
        """
        all_inputs: Dict[str, Dict[str, Any]] = {}

        for device in devices:
            # Start with device's custom_variables and structured_config
            device_vars = deepcopy(device.custom_variables)

            # Add required device fields
            device_vars.update(
                {
                    "hostname": device.hostname,
                    "platform": device.platform,
                    "mgmt_ip": str(device.mgmt_ip),
                    "type": device.device_type,  # 'type' is the AVD key for device_type
                }
            )

            # Add optional fields if present
            if device.mgmt_gateway:
                device_vars["mgmt_gateway"] = str(device.mgmt_gateway)
            if device.serial_number:
                device_vars["serial_number"] = device.serial_number
            if device.system_mac_address:
                device_vars["system_mac_address"] = device.system_mac_address
            if device.pod:
                device_vars["pod"] = device.pod
            if device.rack:
                device_vars["rack"] = device.rack

            # Add fabric information
            device_vars["fabric_name"] = device.fabric

            # Merge structured_config if present
            if device.structured_config:
                device_vars["structured_config"] = deepcopy(device.structured_config)

            all_inputs[device.hostname] = device_vars

        return all_inputs


class DocumentationGenerator:
    """Generator for device documentation.

    This class handles generation of device documentation from AVD inventory
    data using py-avd library.
    """

    def __init__(self, workflow: str = "eos-design") -> None:
        """Initialize the documentation generator.

        Parameters
        ----------
        workflow : str, optional
            Workflow type ('eos-design' or 'cli-config'), by default "eos-design"
        """
        from avd_cli.constants import normalize_workflow

        self.workflow = normalize_workflow(workflow)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate(
        self, inventory: InventoryData, output_path: Path, limit_to_groups: Optional[List[str]] = None
    ) -> List[Path]:
        """Generate device documentation.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data
        output_path : Path
            Output directory for generated docs
        limit_to_groups : Optional[List[str]], optional
            Groups to limit generation to, by default None

        Returns
        -------
        List[Path]
            List of generated documentation file paths

        Raises
        ------
        DocumentationGenerationError
            If generation fails
        """
        self.logger.info("Generating documentation with workflow: %s", self.workflow)

        # Create output directory
        docs_dir = output_path / DEFAULT_DOCS_DIR
        docs_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Import and validate pyavd
            pyavd = self._import_pyavd()

            # Get and filter devices
            devices = self._get_filtered_devices(inventory, limit_to_groups)
            if not devices:
                self.logger.warning("No devices to process")
                return []

            # Build structured configs
            structured_configs = self._build_structured_configs(inventory, devices, pyavd)

            # Generate documentation files
            return self._generate_doc_files(structured_configs, docs_dir, pyavd)

        except DocumentationGenerationError:
            raise
        except Exception as e:
            raise DocumentationGenerationError(f"Failed to generate documentation: {e}") from e

    def _import_pyavd(self):
        """Import pyavd library with error handling."""
        try:
            import pyavd
            return pyavd
        except ImportError as e:
            raise DocumentationGenerationError(
                "pyavd library not installed. Install with: pip install pyavd"
            ) from e

    def _get_filtered_devices(self, inventory: InventoryData, limit_to_groups: Optional[List[str]]):
        """Get devices filtered by groups if specified."""
        devices = inventory.get_all_devices()
        if limit_to_groups:
            devices = [d for d in devices if d.fabric in limit_to_groups]
        return devices

    def _build_structured_configs(self, inventory: InventoryData, devices, pyavd) -> Dict[str, Dict[str, Any]]:
        """Build structured configs based on workflow."""
        from avd_cli.logics.generator import ConfigurationGenerator

        config_gen = ConfigurationGenerator(workflow=self.workflow)
        all_inputs = config_gen._build_pyavd_inputs_from_inventory(inventory, devices)

        if not all_inputs:
            return {}

        structured_configs: Dict[str, Dict[str, Any]] = {}

        if self.workflow == "eos-design":
            structured_configs = self._build_eos_design_configs(all_inputs, pyavd)
        else:  # workflow == "cli-config"
            structured_configs = self._build_cli_config_configs(all_inputs)

        return structured_configs

    def _build_eos_design_configs(self, all_inputs, pyavd) -> Dict[str, Dict[str, Any]]:
        """Build structured configs for eos-design workflow."""
        self.logger.info("Generating AVD facts for documentation")
        avd_facts = pyavd.get_avd_facts(all_inputs)

        structured_configs = {}
        for hostname, inputs in all_inputs.items():
            structured_config = pyavd.get_device_structured_config(
                hostname=hostname, inputs=inputs, avd_facts=avd_facts
            )
            structured_configs[hostname] = structured_config

        return structured_configs

    def _build_cli_config_configs(self, all_inputs) -> Dict[str, Dict[str, Any]]:
        """Build structured configs for cli-config workflow."""
        self.logger.info("Using existing structured configs for documentation")
        # For cli-config, inputs ARE the structured configs
        return dict(all_inputs)

    def _generate_doc_files(self, structured_configs: Dict[str, Dict[str, Any]], docs_dir: Path, pyavd) -> List[Path]:
        """Generate documentation files from structured configs."""
        self.logger.info("Generating device documentation")
        generated_files: List[Path] = []

        for hostname, structured_config in structured_configs.items():
            doc_file = docs_dir / f"{hostname}.md"
            doc_text = pyavd.get_device_doc(structured_config, add_md_toc=True)

            with open(doc_file, "w", encoding="utf-8") as f:
                f.write(doc_text)

            generated_files.append(doc_file)
            self.logger.debug("Generated doc: %s", doc_file)

        self.logger.info("Generated %d documentation files", len(generated_files))
        return generated_files


class TestGenerator:
    """Generator for test files (ANTA).

    This class handles generation of ANTA test files from AVD inventory data.
    """

    def __init__(self, test_type: str = "anta") -> None:
        """Initialize the test generator.

        Parameters
        ----------
        test_type : str, optional
            Test type ('anta' or 'robot'), by default "anta"
        """
        self.test_type = test_type
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate(
        self, inventory: InventoryData, output_path: Path, limit_to_groups: Optional[List[str]] = None
    ) -> List[Path]:
        """Generate test files.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data
        output_path : Path
            Output directory for generated tests
        limit_to_groups : Optional[List[str]], optional
            Groups to limit generation to, by default None

        Returns
        -------
        List[Path]
            List of generated test file paths

        Raises
        ------
        TestGenerationError
            If generation fails
        """
        self.logger.info("Generating %s tests", self.test_type.upper())

        # Create output directory
        tests_dir = output_path / DEFAULT_TESTS_DIR
        tests_dir.mkdir(parents=True, exist_ok=True)

        generated_files: List[Path] = []

        try:
            devices = inventory.get_all_devices()

            # Filter by groups if specified
            if limit_to_groups:
                devices = [d for d in devices if d.fabric in limit_to_groups]

            # TODO: Implement actual test generation
            test_file = tests_dir / "devices_tests.yaml"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("---\n")
                f.write(f"# {self.test_type.upper()} Tests\n")
                f.write("# Generated by avd-cli (placeholder)\n\n")
                f.write("anta.tests.connectivity:\n")
                for device in devices:
                    f.write("  - VerifyReachability:\n")
                    f.write("      hosts:\n")
                    f.write(f"        - destination: {device.mgmt_ip}\n")
                    f.write("          source: Management1\n")
            generated_files.append(test_file)

            self.logger.info("Generated %d test files", len(generated_files))
            return generated_files

        except Exception as e:
            raise TestGenerationError(f"Failed to generate tests: {e}") from e


def generate_all(
    inventory: InventoryData,
    output_path: Path,
    workflow: str = "eos-design",
    limit_to_groups: Optional[List[str]] = None,
) -> Tuple[List[Path], List[Path], List[Path]]:
    """Generate all outputs: configurations, documentation, and tests.

    Parameters
    ----------
    inventory : InventoryData
        Loaded inventory data
    output_path : Path
        Output directory for all generated files
    workflow : str, optional
        Workflow type, by default "eos-design"
        Legacy values 'full' and 'config-only' are also supported for backward compatibility.
    limit_to_groups : Optional[List[str]], optional
        Groups to limit generation to, by default None

    Returns
    -------
    Tuple[List[Path], List[Path], List[Path]]
        Tuple of (config_files, doc_files, test_files)
    """
    from avd_cli.constants import normalize_workflow

    workflow = normalize_workflow(workflow)

    config_gen = ConfigurationGenerator(workflow=workflow)
    doc_gen = DocumentationGenerator(workflow=workflow)
    test_gen = TestGenerator()

    configs = config_gen.generate(inventory, output_path, limit_to_groups)
    docs = doc_gen.generate(inventory, output_path, limit_to_groups)
    tests = test_gen.generate(inventory, output_path, limit_to_groups)

    return configs, docs, tests
