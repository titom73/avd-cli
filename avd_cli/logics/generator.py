#!/usr/bin/env python
# coding: utf-8 -*-

"""Configuration generation functionality.

This module provides functionality to generate device configurations,
documentation, and test files from AVD inventory data.
"""

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from rich.console import Console

from avd_cli.constants import (DEFAULT_CONFIGS_DIR, DEFAULT_DOCS_DIR,
                               DEFAULT_TESTS_DIR, normalize_workflow)
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
        """
        self.workflow = normalize_workflow(workflow)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.pyavd: Any = None  # Will be initialized when needed

    def _setup_generation(self, output_path: Path) -> Path:
        """Setup directories and import pyavd for generation."""
        # Import pyavd
        try:
            import pyavd
            self.pyavd = pyavd
        except ImportError as e:
            raise ConfigurationGenerationError(
                "pyavd library not installed. Install with: pip install pyavd"
            ) from e

        # Create output directory
        configs_dir = output_path / DEFAULT_CONFIGS_DIR
        configs_dir.mkdir(parents=True, exist_ok=True)
        return configs_dir

    def _filter_devices(self, inventory: InventoryData, limit_to_groups: Optional[List[str]]) -> List[DeviceDefinition]:
        """Filter devices by groups if specified."""
        devices = inventory.get_all_devices()
        if limit_to_groups:
            # Filter by fabric name OR by any group membership
            devices = [
                d for d in devices
                if d.fabric in limit_to_groups or any(g in limit_to_groups for g in d.groups)
            ]
            self.logger.info("Limited to %d devices in groups: %s", len(devices), limit_to_groups)
        return devices

    def _generate_structured_configs(self, all_inputs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Generate structured configurations based on workflow."""
        structured_configs: Dict[str, Dict[str, Any]] = {}

        if self.workflow == "eos-design":
            # Validate inputs first
            self.logger.info("Validating inputs against eos_designs schema")
            for hostname, inputs in all_inputs.items():
                validation_result = self.pyavd.validate_inputs(inputs)
                if validation_result.failed:
                    errors = "\n".join(str(e) for e in validation_result.validation_errors)
                    raise ConfigurationGenerationError(
                        f"Input validation failed for {hostname}:\n{errors}"
                    )
                if validation_result.deprecation_warnings:
                    for warning in validation_result.deprecation_warnings:
                        self.logger.warning("Deprecation warning for %s: %s", hostname, warning)

            # Generate AVD facts and structured configs
            self.logger.info("Generating AVD facts for %d devices", len(all_inputs))
            avd_facts = self.pyavd.get_avd_facts(all_inputs)

            self.logger.info("Generating structured configurations")
            for hostname, inputs in all_inputs.items():
                structured_config = self.pyavd.get_device_structured_config(
                    hostname=hostname, inputs=inputs, avd_facts=avd_facts
                )
                structured_configs[hostname] = structured_config
        else:
            # Config-only workflow (cli-config)
            self.logger.info("Using cli-config workflow (eos_cli_config_gen only)")
            for hostname, inputs in all_inputs.items():
                structured_configs[hostname] = inputs

        return structured_configs

    def _write_config_files(self, structured_configs: Dict[str, Dict[str, Any]], configs_dir: Path) -> List[Path]:
        """Write configuration files to disk."""
        generated_files: List[Path] = []

        # Validate structured configs
        self.logger.info("Validating structured configurations")
        for hostname, structured_config in structured_configs.items():
            validation_result = self.pyavd.validate_structured_config(structured_config)
            if validation_result.failed:
                errors = "\n".join(str(e) for e in validation_result.validation_errors)
                raise ConfigurationGenerationError(
                    f"Structured config validation failed for {hostname}:\n{errors}"
                )

        # Generate EOS CLI configurations
        self.logger.info("Generating EOS CLI configurations")
        for hostname, structured_config in structured_configs.items():
            config_file = configs_dir / f"{hostname}.cfg"
            config_text = self.pyavd.get_device_config(structured_config)

            with open(config_file, "w", encoding="utf-8") as f:
                f.write(config_text)

            generated_files.append(config_file)
            self.logger.debug("Generated config: %s", config_file)

        return generated_files

    def generate(
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

        configs_dir = self._setup_generation(output_path)

        try:
            devices = self._filter_devices(inventory, limit_to_groups)

            # Build pyavd inputs from inventory
            self.logger.info("Building pyavd inputs from resolved inventory")
            all_inputs = self._build_pyavd_inputs_from_inventory(inventory, devices)

            if not all_inputs:
                self.logger.warning("No devices to process")
                return []

            structured_configs = self._generate_structured_configs(all_inputs)
            generated_files = self._write_config_files(structured_configs, configs_dir)

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

        This reuses the InventoryLoader's variable resolution (including Jinja2 templates)
        and builds the input structure expected by pyavd.

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
        all_inputs: Dict[str, Dict[str, Any]] = {}

        for device in devices:
            device_vars: Dict[str, Any] = {}

            # Start with global variables
            device_vars = deepcopy(inventory.global_vars)

            # Merge ALL group variables (already resolved by InventoryLoader)
            # We merge all groups because we don't track the exact group hierarchy
            for group_name in sorted(inventory.group_vars.keys()):
                device_vars = self._deep_merge(device_vars, inventory.group_vars[group_name])

            # Merge host-specific variables (highest priority, already resolved)
            if device.hostname in inventory.host_vars:
                device_vars = self._deep_merge(device_vars, inventory.host_vars[device.hostname])

            # Convert numeric strings to actual numbers (for pyavd schema validation)
            # This handles Jinja2 templates that resolve to string numbers
            device_vars = self._convert_numeric_strings(device_vars)

            # Ensure hostname is present (required by pyavd)
            device_vars.setdefault("hostname", device.hostname)

            # Only set type if not already defined in variables
            # AVD group_vars should define the correct type (l3leaf, l2leaf, spine, etc.)
            if "type" not in device_vars:
                self.logger.warning(
                    "Device %s has no 'type' defined in AVD variables, using inventory type: %s",
                    device.hostname,
                    device.device_type,
                )
                device_vars["type"] = device.device_type

            # Extract node ID from AVD topology structure (required by pyavd)
            # The ID is nested in l2leaf/l3spine/spine/leaf node_groups
            if "id" not in device_vars:
                node_id = self._extract_node_id(device_vars, device.hostname)
                if node_id is not None:
                    device_vars["id"] = node_id
                    self.logger.info("Extracted node ID %s for device %s", node_id, device.hostname)
                else:
                    self.logger.warning(
                        "Device %s has no 'id' defined in AVD topology structure", device.hostname
                    )

            all_inputs[device.hostname] = device_vars

        return all_inputs

    def _convert_inventory_to_pyavd_inputs(
        self, inventory: InventoryData, devices: List[DeviceDefinition]
    ) -> Dict[str, Dict[str, Any]]:
        """Build pyavd inputs from resolved inventory data (legacy wrapper).

        This is a backward-compatibility wrapper for the renamed method.

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

        See Also
        --------
        _build_pyavd_inputs_from_inventory : New method name
        """
        return self._build_pyavd_inputs_from_inventory(inventory, devices)

    def _find_node_in_groups(self, node_groups: List[Any], hostname: str) -> Union[int, None]:
        """Search through node groups for a hostname and return its ID."""
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
                        return self._validate_node_id(node_id, hostname)
        return None

    def _validate_node_id(self, node_id: Any, hostname: str) -> Union[int, None]:
        """Validate and convert node ID to integer."""
        try:
            return int(node_id)
        except (ValueError, TypeError):
            self.logger.warning(
                "Invalid node ID '%s' for device %s", node_id, hostname
            )
            return None

    def _determine_device_type(self, device_vars: Dict[str, Any], hostname: str) -> Union[str, None]:
        """Determine device type from AVD topology structure.

        Parameters
        ----------
        device_vars : Dict[str, Any]
            Device variables containing AVD topology structure
        hostname : str
            Hostname to find type for

        Returns
        -------
        str | None
            Device type (spine, leaf, etc.) if found, None otherwise
        """
        # Look for common AVD topology keys
        topology_keys = ["l2leaf", "l3spine", "spine", "leaf", "super_spine"]

        for topology_key in topology_keys:
            topology_data = device_vars.get(topology_key)
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
                        # Return the device type (topology_key)
                        # Map l2leaf/l3spine to leaf/spine for consistency
                        type_mapping = {
                            "l2leaf": "leaf",
                            "l3spine": "spine",
                            "spine": "spine",
                            "leaf": "leaf",
                            "super_spine": "super_spine"
                        }
                        return type_mapping.get(topology_key, topology_key)

        return None

    def _extract_node_id(self, device_vars: Dict[str, Any], hostname: str) -> Union[int, None]:
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
            topology_data = device_vars.get(topology_key)
            if not isinstance(topology_data, dict):
                continue

            node_groups = topology_data.get("node_groups", [])
            if not isinstance(node_groups, list):
                continue

            result = self._find_node_in_groups(node_groups, hostname)
            if result is not None:
                return result

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


class DocumentationGenerator:
    """Generator for device documentation.

    This class handles generation of device documentation from AVD inventory
    data using py-avd library.
    """

    def __init__(self) -> None:
        """Initialize the documentation generator."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.pyavd: Any = None

    def _import_pyavd(self) -> Any:
        """Import pyavd library.

        Returns
        -------
        Any
            pyavd module

        Raises
        ------
        DocumentationGenerationError
            If pyavd is not installed
        """
        try:
            import pyavd
            return pyavd
        except ImportError as e:
            raise DocumentationGenerationError(
                "pyavd library not installed. Install with: pip install pyavd"
            ) from e

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
        self.logger.info("Generating documentation")

        # Create output directory
        docs_dir = output_path / DEFAULT_DOCS_DIR
        docs_dir.mkdir(parents=True, exist_ok=True)

        generated_files: List[Path] = []

        try:
            # Import pyavd
            pyavd = self._import_pyavd()

            devices = inventory.get_all_devices()

            # Filter by groups if specified
            if limit_to_groups:
                devices = [d for d in devices if d.fabric in limit_to_groups]

            # Reuse the conversion logic from ConfigurationGenerator
            from avd_cli.logics.generator import ConfigurationGenerator

            config_gen = ConfigurationGenerator(workflow="eos-design")
            all_inputs = config_gen._build_pyavd_inputs_from_inventory(inventory, devices)

            if not all_inputs:
                self.logger.warning("No devices to process")
                return generated_files

            # Generate AVD facts and structured configs
            self.logger.info("Generating AVD facts for documentation")
            avd_facts = pyavd.get_avd_facts(all_inputs)

            structured_configs: Dict[str, Dict[str, Any]] = {}
            for hostname, inputs in all_inputs.items():
                structured_config = pyavd.get_device_structured_config(
                    hostname=hostname, inputs=inputs, avd_facts=avd_facts
                )
                structured_configs[hostname] = structured_config

            # Generate device documentation
            self.logger.info("Generating device documentation")
            for hostname, structured_config in structured_configs.items():
                doc_file = docs_dir / f"{hostname}.md"
                doc_text = pyavd.get_device_doc(structured_config, add_md_toc=True)

                with open(doc_file, "w", encoding="utf-8") as f:
                    f.write(doc_text)

                generated_files.append(doc_file)
                self.logger.debug("Generated doc: %s", doc_file)

            self.logger.info("Generated %d documentation files", len(generated_files))
            return generated_files

        except DocumentationGenerationError:
            raise
        except Exception as e:
            raise DocumentationGenerationError(f"Failed to generate documentation: {e}") from e


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
    limit_to_groups : Optional[List[str]], optional
        Groups to limit generation to, by default None

    Returns
    -------
    Tuple[List[Path], List[Path], List[Path]]
        Tuple of (config_files, doc_files, test_files)
    """
    config_gen = ConfigurationGenerator(workflow=normalize_workflow(workflow))
    doc_gen = DocumentationGenerator()
    test_gen = TestGenerator()

    configs = config_gen.generate(inventory, output_path, limit_to_groups)
    docs = doc_gen.generate(inventory, output_path, limit_to_groups)
    tests = test_gen.generate(inventory, output_path, limit_to_groups)

    return configs, docs, tests
