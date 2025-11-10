#!/usr/bin/env python
# coding: utf-8 -*-

"""Inventory loading functionality.

This module provides functionality to load AVD inventories from YAML files
and convert them into structured data models.
"""

import logging
from ipaddress import ip_address
from pathlib import Path
from typing import Any, Dict, List, Set, Union

import yaml

from avd_cli.constants import INVENTORY_GROUP_VARS_DIR, INVENTORY_HOST_VARS_DIR
from avd_cli.exceptions import FileSystemError, InvalidInventoryError
from avd_cli.logics.templating import TemplateResolver, build_template_context
from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData

logger = logging.getLogger(__name__)

# Device type mapping: AVD types -> Canonical types
DEVICE_TYPE_MAPPING = {
    "l3spine": "spine",
    "l2leaf": "leaf",
    "l3leaf": "leaf",
    # Canonical types map to themselves
    "spine": "spine",
    "leaf": "leaf",
    "border_leaf": "border_leaf",
    "super_spine": "super_spine",
    "overlay_controller": "overlay_controller",
    "wan_router": "wan_router",
}


class InventoryLoader:
    """Loader for AVD inventory structures.

    This class handles loading and parsing AVD inventory files from disk,
    validating the directory structure, and converting YAML data into
    structured data models.

    Examples
    --------
    >>> loader = InventoryLoader()
    >>> inventory = loader.load(Path("./inventory"))
    >>> print(f"Loaded {len(inventory.get_all_devices())} devices")
    """

    def __init__(self) -> None:
        """Initialize the inventory loader."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def load(self, inventory_path: Path) -> InventoryData:
        """Load AVD inventory from directory.

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        InventoryData
            Loaded inventory data structure

        Raises
        ------
        InvalidInventoryError
            If inventory structure is invalid
        FileSystemError
            If inventory directory cannot be read
        """
        self.logger.info("Loading inventory from: %s", inventory_path)

        # Validate directory exists and is readable
        self._validate_inventory_path(inventory_path)

        # Load global variables
        global_vars = self._load_global_vars(inventory_path)

        # Load group variables from group_vars/
        group_vars = self._load_group_vars(inventory_path)

        # Load group variables from inventory.yml and merge
        inventory_group_vars = self._load_inventory_group_vars(inventory_path)
        for group_name, group_data in inventory_group_vars.items():
            if group_name in group_vars:
                # Merge: group_vars/ files take precedence over inventory.yml
                merged = {**group_data, **group_vars[group_name]}
                group_vars[group_name] = merged
            else:
                group_vars[group_name] = group_data

        # Load host variables from host_vars/
        host_vars = self._load_host_vars(inventory_path)

        # Load hosts from inventory.yml and merge with host_vars
        inventory_hosts = self._load_inventory_hosts(inventory_path)
        for hostname, host_data in inventory_hosts.items():
            if hostname in host_vars:
                # Merge: host_vars takes precedence
                merged = {**host_data, **host_vars[hostname]}
                host_vars[hostname] = merged
            else:
                host_vars[hostname] = host_data

        self.logger.info(
            "Loaded: %d global vars, %d groups, %d hosts",
            len(global_vars),
            len(group_vars),
            len(host_vars),
        )

        # Build template context BEFORE resolving templates
        # This allows templates to reference hostvars that include group vars
        self.logger.debug("Building template context with enriched hostvars")
        context = build_template_context(global_vars, group_vars, host_vars)

        # Resolve Jinja2 templates in multiple passes
        # This handles nested templates (templates that reference other templates)
        self.logger.debug("Resolving Jinja2 templates in inventory variables")
        max_passes = 5  # Prevent infinite loops
        for pass_num in range(max_passes):
            # Rebuild context with partially resolved variables
            context = build_template_context(global_vars, group_vars, host_vars)
            resolver = TemplateResolver(context)

            # Resolve templates in all variable dictionaries
            new_global_vars = resolver.resolve_recursive(global_vars)
            new_group_vars = {name: resolver.resolve_recursive(data) for name, data in group_vars.items()}
            new_host_vars = {name: resolver.resolve_recursive(data) for name, data in host_vars.items()}

            # Check if anything changed (templates resolved)
            if (
                new_global_vars == global_vars
                and new_group_vars == group_vars
                and new_host_vars == host_vars
            ):
                self.logger.debug("Template resolution complete after %d passes", pass_num + 1)
                break

            global_vars = new_global_vars
            group_vars = new_group_vars
            host_vars = new_host_vars
        else:
            self.logger.warning(
                "Template resolution reached max passes (%d), some templates may remain unresolved",
                max_passes,
            )

        # Build group hierarchy map from inventory structure
        group_hierarchy = self._build_group_hierarchy(inventory_path)

        # Build hostname-to-group mapping from inventory structure
        host_to_group = self._build_host_to_group_map(inventory_path)

        # Parse loaded data into DeviceDefinition and FabricDefinition objects
        fabrics = self._parse_fabrics(global_vars, group_vars, host_vars, group_hierarchy, host_to_group)

        # Create inventory data structure with resolved variables
        inventory = InventoryData(
            root_path=inventory_path,
            fabrics=fabrics,
            global_vars=global_vars,
            group_vars=group_vars,
            host_vars=host_vars,
        )

        return inventory

    def _validate_inventory_path(self, inventory_path: Path) -> None:
        """Validate inventory directory exists and is readable.

        Parameters
        ----------
        inventory_path : Path
            Path to validate

        Raises
        ------
        FileSystemError
            If path doesn't exist or isn't a directory
        InvalidInventoryError
            If inventory structure is invalid
        """
        if not inventory_path.exists():
            raise FileSystemError(f"Inventory path does not exist: {inventory_path}")

        if not inventory_path.is_dir():
            raise FileSystemError(f"Inventory path is not a directory: {inventory_path}")

        # Check for at least one of group_vars or host_vars
        group_vars_path = inventory_path / INVENTORY_GROUP_VARS_DIR
        host_vars_path = inventory_path / INVENTORY_HOST_VARS_DIR

        if not group_vars_path.exists() and not host_vars_path.exists():
            raise InvalidInventoryError(
                f"Inventory must contain at least one of: {INVENTORY_GROUP_VARS_DIR}, {INVENTORY_HOST_VARS_DIR}"
            )

    def _load_global_vars(self, inventory_path: Path) -> Dict[str, Any]:
        """Load global variables from inventory.

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, Any]
            Global variables
        """
        global_vars: Dict[str, Any] = {}

        # Check for all.yml in group_vars
        all_yml = inventory_path / INVENTORY_GROUP_VARS_DIR / "all.yml"
        if all_yml.exists():
            try:
                with open(all_yml, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        global_vars.update(data)
                self.logger.debug("Loaded global vars from: %s", all_yml)
            except yaml.YAMLError as e:
                raise InvalidInventoryError(f"Invalid YAML in {all_yml}: {e}") from e
            except OSError as e:
                raise FileSystemError(f"Cannot read {all_yml}: {e}") from e

        return global_vars

    def _load_group_vars(self, inventory_path: Path) -> Dict[str, Dict[str, Any]]:
        """Load group variables from group_vars directory.

        Supports both file and directory formats:
        - group_vars/FABRIC.yml (file)
        - group_vars/FABRIC/ (directory with multiple YAML files)

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping group names to their variables
        """
        group_vars: Dict[str, Dict[str, Any]] = {}
        group_vars_path = inventory_path / INVENTORY_GROUP_VARS_DIR

        if not group_vars_path.exists():
            return group_vars

        try:
            # Iterate through all entries in group_vars
            for entry in group_vars_path.iterdir():
                if entry.name == "all.yml" or entry.name == "all":
                    continue  # Already loaded in global_vars

                if entry.is_file() and entry.suffix in [".yml", ".yaml"]:
                    # Single file format
                    group_name = entry.stem
                    group_vars[group_name] = self._load_yaml_file(entry)
                    self.logger.debug("Loaded group vars for: %s (file)", group_name)

                elif entry.is_dir():
                    # Directory format - merge all YAML files
                    group_name = entry.name
                    group_vars[group_name] = self._load_yaml_directory(entry)
                    self.logger.debug("Loaded group vars for: %s (directory)", group_name)

        except OSError as e:
            raise FileSystemError(f"Cannot read group_vars directory: {e}") from e

        return group_vars

    def _load_host_vars(self, inventory_path: Path) -> Dict[str, Dict[str, Any]]:
        """Load host variables from host_vars directory.

        Supports both file and directory formats:
        - host_vars/spine1.yml (file)
        - host_vars/spine1/ (directory with multiple YAML files)

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping hostnames to their variables
        """
        host_vars: Dict[str, Dict[str, Any]] = {}
        host_vars_path = inventory_path / INVENTORY_HOST_VARS_DIR

        if not host_vars_path.exists():
            return host_vars

        try:
            # Iterate through all entries in host_vars
            for entry in host_vars_path.iterdir():
                if entry.is_file() and entry.suffix in [".yml", ".yaml"]:
                    # Single file format
                    hostname = entry.stem
                    host_vars[hostname] = self._load_yaml_file(entry)
                    self.logger.debug("Loaded host vars for: %s (file)", hostname)

                elif entry.is_dir():
                    # Directory format - merge all YAML files
                    hostname = entry.name
                    host_vars[hostname] = self._load_yaml_directory(entry)
                    self.logger.debug("Loaded host vars for: %s (directory)", hostname)

        except OSError as e:
            raise FileSystemError(f"Cannot read host_vars directory: {e}") from e

        return host_vars

    def _load_inventory_hosts(self, inventory_path: Path) -> Dict[str, Dict[str, Any]]:
        """Load host definitions from inventory.yml.

        Extracts host variables (like ansible_host) from the inventory.yml file
        by recursively traversing the children/hosts structure.

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping hostnames to their variables from inventory.yml
        """
        inventory_hosts: Dict[str, Dict[str, Any]] = {}
        inventory_yml = inventory_path / "inventory.yml"

        if not inventory_yml.exists():
            # Try .yaml extension
            inventory_yml = inventory_path / "inventory.yaml"
            if not inventory_yml.exists():
                return inventory_hosts

        try:
            inventory_data = self._load_yaml_file(inventory_yml)
            self._extract_hosts_recursive(inventory_data, inventory_hosts)
            self.logger.debug("Extracted %d hosts from inventory.yml", len(inventory_hosts))
        except Exception as e:
            self.logger.warning("Failed to extract hosts from inventory.yml: %s", e)

        return inventory_hosts

    def _load_inventory_group_vars(self, inventory_path: Path) -> Dict[str, Dict[str, Any]]:
        """Load group variables from inventory.yml.

        Extracts group vars from the inventory.yml file by traversing the structure
        and collecting all 'vars' sections.

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping group names to their variables from inventory.yml
        """
        inventory_group_vars: Dict[str, Dict[str, Any]] = {}
        inventory_yml = inventory_path / "inventory.yml"

        if not inventory_yml.exists():
            inventory_yml = inventory_path / "inventory.yaml"
            if not inventory_yml.exists():
                return inventory_group_vars

        try:
            inventory_data = self._load_yaml_file(inventory_yml)
            self._extract_group_vars_recursive(inventory_data, inventory_group_vars, current_group="root")
            self.logger.debug("Extracted group vars for %d groups from inventory.yml",
                              len(inventory_group_vars))
        except Exception as e:
            self.logger.warning("Failed to extract group vars from inventory.yml: %s", e)

        return inventory_group_vars

    def _extract_group_vars_recursive(
        self,
        data: Any,
        result: Dict[str, Dict[str, Any]],
        current_group: str,
    ) -> None:
        """Recursively extract group vars from inventory structure.

        Parameters
        ----------
        data : Any
            Current level of inventory data
        result : Dict[str, Dict[str, Any]]
            Dictionary to populate with found group vars
        current_group : str
            Name of current group being processed
        """
        if not isinstance(data, dict):
            return

        # Check if this level has 'vars'
        if "vars" in data and isinstance(data["vars"], dict):
            if current_group not in result:
                result[current_group] = {}
            result[current_group].update(data["vars"])

        # Recurse into children
        if "children" in data and isinstance(data["children"], dict):
            for child_name, child_data in data["children"].items():
                self._extract_group_vars_recursive(child_data, result, child_name)

        # Also check any other dict values that might be groups
        for key, value in data.items():
            if key not in ["hosts", "children", "vars"] and isinstance(value, dict):
                self._extract_group_vars_recursive(value, result, key)

    def _build_group_hierarchy(self, inventory_path: Path) -> Dict[str, List[str]]:
        """Build a map of group names to ALL their ancestor groups (including self).

        This parses the inventory.yml structure to understand group parent-child
        relationships. A group can have multiple parents in Ansible, so we collect
        ALL ancestors, not just one path.

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, List[str]]
            Dictionary mapping each group name to sorted list of ALL its ancestor groups
            (e.g., {"campus_leaves": ["atd", "campus_avd", "campus_leaves", "campus_ports", "campus_services", "lab"]})
        """
        inventory_yml = inventory_path / "inventory.yml"
        if not inventory_yml.exists():
            inventory_yml = inventory_path / "inventory.yaml"
            if not inventory_yml.exists():
                self.logger.warning("No inventory.yml found, cannot build group hierarchy")
                return {}

        try:
            inventory_data = self._load_yaml_file(inventory_yml)
        except Exception as e:
            self.logger.warning("Failed to load inventory.yml for hierarchy: %s", e)
            return {}

        # First pass: build all paths
        all_paths: Dict[str, List[List[str]]] = {}
        self._extract_all_paths_recursive(inventory_data, all_paths, [])

        # Second pass: flatten to sets of all ancestors, then convert to sorted lists
        hierarchy_sets: Dict[str, Set[str]] = {}
        for group_name, paths in all_paths.items():
            ancestors = set()
            for path in paths:
                ancestors.update(path)
            hierarchy_sets[group_name] = ancestors

        # Convert sets to sorted lists for consistent ordering
        hierarchy: Dict[str, List[str]] = {
            group: sorted(ancestors) for group, ancestors in hierarchy_sets.items()
        }

        self.logger.debug("Built hierarchy for %d groups", len(hierarchy))
        return hierarchy

    def _extract_all_paths_recursive(
        self,
        data: Any,
        result: Dict[str, List[List[str]]],
        current_path: List[str],
    ) -> None:
        """Recursively extract ALL paths to each group (handles multiple parents).

        Parameters
        ----------
        data : Any
            Current level of inventory data
        result : Dict[str, List[List[str]]]
            Dictionary to populate with all paths to each group
        current_path : List[str]
            Current path from root to this level
        """
        if not isinstance(data, dict):
            return

        # Process children groups
        if "children" in data and isinstance(data["children"], dict):
            for child_name, child_data in data["children"].items():
                # Add this path for the child
                child_path = current_path + [child_name]
                if child_name not in result:
                    result[child_name] = []
                result[child_name].append(child_path)
                # Recurse into child
                self._extract_all_paths_recursive(child_data, result, child_path)

        # Also check top-level groups (like 'lab', 'all', etc.)
        for key, value in data.items():
            if key not in ["hosts", "children", "vars"] and isinstance(value, dict):
                if key not in result:
                    # This is a root-level group
                    result[key] = [[key]]
                self._extract_all_paths_recursive(value, result, [key])

    def _extract_hierarchy_recursive(
        self,
        data: Any,
        result: Dict[str, List[str]],
        ancestors: List[str],
    ) -> None:
        """Recursively build group hierarchy by traversing inventory structure.

        Parameters
        ----------
        data : Any
            Current level of inventory data
        result : Dict[str, List[str]]
            Dictionary to populate with group hierarchies
        ancestors : List[str]
            List of ancestor group names from root to current level
        """
        if not isinstance(data, dict):
            return

        # Process children groups
        if "children" in data and isinstance(data["children"], dict):
            for child_name, child_data in data["children"].items():
                # Record this child's full ancestry (ancestors + self)
                child_ancestors = ancestors + [child_name]
                result[child_name] = child_ancestors
                # Recurse into child
                self._extract_hierarchy_recursive(child_data, result, child_ancestors)

        # Also check top-level groups (like 'lab', 'all', etc.)
        for key, value in data.items():
            if key not in ["hosts", "children", "vars"] and isinstance(value, dict):
                if key not in result:
                    # This is a root-level group
                    group_ancestors = [key]
                    result[key] = group_ancestors
                    self._extract_hierarchy_recursive(value, result, group_ancestors)

    def _build_host_to_group_map(self, inventory_path: Path) -> Dict[str, str]:
        """Build a map of hostnames to their immediate Ansible group.

        This finds where each host is defined in the inventory.yml structure
        (e.g., leaf-1a -> IDF1, spine01 -> campus_spines).

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, str]
            Dictionary mapping hostname to its immediate group name
        """
        inventory_yml = inventory_path / "inventory.yml"
        if not inventory_yml.exists():
            inventory_yml = inventory_path / "inventory.yaml"
            if not inventory_yml.exists():
                self.logger.warning("No inventory.yml found, cannot build host-to-group map")
                return {}

        try:
            inventory_data = self._load_yaml_file(inventory_yml)
        except Exception as e:
            self.logger.warning("Failed to load inventory.yml for host mapping: %s", e)
            return {}

        host_map: Dict[str, str] = {}
        self._extract_host_groups_recursive(inventory_data, host_map, current_group="root")
        self.logger.debug("Built host-to-group map for %d hosts", len(host_map))
        return host_map

    def _extract_host_groups_recursive(
        self,
        data: Any,
        result: Dict[str, str],
        current_group: str,
    ) -> None:
        """Recursively find hosts and record their immediate group.

        Parameters
        ----------
        data : Any
            Current level of inventory data
        result : Dict[str, str]
            Dictionary to populate with hostname -> group mappings
        current_group : str
            Name of current group being processed
        """
        if not isinstance(data, dict):
            return

        # Check if this level has 'hosts'
        if "hosts" in data and isinstance(data["hosts"], dict):
            for hostname in data["hosts"].keys():
                # Record this host's immediate group
                result[hostname] = current_group

        # Recurse into children
        if "children" in data and isinstance(data["children"], dict):
            for child_name, child_data in data["children"].items():
                self._extract_host_groups_recursive(child_data, result, child_name)

        # Also check any other dict values that might be groups
        for key, value in data.items():
            if key not in ["hosts", "children", "vars"] and isinstance(value, dict):
                self._extract_host_groups_recursive(value, result, key)

    def _extract_hosts_recursive(
        self,
        data: Any,
        result: Dict[str, Dict[str, Any]],
        parent_vars: Union[Dict[str, Any], None] = None,
    ) -> None:
        """Recursively extract hosts from inventory structure with inherited vars.

        Parameters
        ----------
        data : Any
            Current level of inventory data
        result : Dict[str, Dict[str, Any]]
            Dictionary to populate with found hosts
        parent_vars : Dict[str, Any], optional
            Variables inherited from parent groups
        """
        if not isinstance(data, dict):
            return

        # Start with parent vars or empty dict
        current_vars = dict(parent_vars) if parent_vars else {}

        # Merge vars at this level
        if "vars" in data and isinstance(data["vars"], dict):
            current_vars.update(data["vars"])

        # Check if this level has 'hosts'
        if "hosts" in data and isinstance(data["hosts"], dict):
            for hostname, host_data in data["hosts"].items():
                # Merge: parent group vars + host vars
                if isinstance(host_data, dict):
                    result[hostname] = {**current_vars, **host_data}
                else:
                    result[hostname] = dict(current_vars)

        # Recurse into children with accumulated vars
        if "children" in data and isinstance(data["children"], dict):
            for child_data in data["children"].values():
                self._extract_hosts_recursive(child_data, result, current_vars)

        # Also check any other dict values that might contain groups
        for key, value in data.items():
            if key not in ["hosts", "children", "vars"] and isinstance(value, dict):
                self._extract_hosts_recursive(value, result, current_vars)

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a single YAML file.

        Parameters
        ----------
        file_path : Path
            Path to YAML file

        Returns
        -------
        Dict[str, Any]
            Loaded data

        Raises
        ------
        InvalidInventoryError
            If YAML is invalid
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            raise InvalidInventoryError(f"Invalid YAML in {file_path}: {e}") from e
        except OSError as e:
            raise FileSystemError(f"Cannot read {file_path}: {e}") from e

    def _load_yaml_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Load and merge all YAML files from a directory.

        Files are processed in alphabetical order, with later files
        overriding earlier ones for duplicate keys (deep merge).

        Parameters
        ----------
        dir_path : Path
            Path to directory containing YAML files

        Returns
        -------
        Dict[str, Any]
            Merged data from all files

        Raises
        ------
        InvalidInventoryError
            If any YAML is invalid
        """
        merged_data: Dict[str, Any] = {}

        # Get all YAML files and sort alphabetically
        yaml_files = sorted(
            [f for f in dir_path.iterdir() if f.is_file() and f.suffix in [".yml", ".yaml"]]
        )

        for yaml_file in yaml_files:
            file_data = self._load_yaml_file(yaml_file)
            merged_data = self._deep_merge(merged_data, file_data)
            self.logger.debug("  Merged: %s", yaml_file.name)

        return merged_data

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.

        Recursively merges nested dictionaries. Later values override earlier ones.
        Lists are replaced, not merged.

        Parameters
        ----------
        base : Dict[str, Any]
            Base dictionary (earlier file)
        override : Dict[str, Any]
            Override dictionary (later file)

        Returns
        -------
        Dict[str, Any]
            Merged dictionary

        Examples
        --------
        >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> override = {"b": {"d": 4, "e": 5}, "f": 6}
        >>> deep_merge(base, override)
        {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override or add new key (lists are replaced, not merged)
                result[key] = value

        return result

    def _normalize_device_type(self, device_type: str) -> str:
        """Normalize AVD device type to canonical type.

        Maps AVD-specific device types (l3spine, l2leaf, l3leaf) to canonical
        types (spine, leaf) for internal processing.

        Parameters
        ----------
        device_type : str
            Device type from inventory (may be AVD-specific or canonical)

        Returns
        -------
        str
            Canonical device type

        Examples
        --------
        >>> loader._normalize_device_type("l3spine")
        "spine"
        >>> loader._normalize_device_type("l2leaf")
        "leaf"
        >>> loader._normalize_device_type("spine")
        "spine"
        """
        normalized = DEVICE_TYPE_MAPPING.get(device_type.lower(), device_type)
        if normalized != device_type:
            self.logger.debug(
                "Mapped device type '%s' to canonical type '%s'", device_type, normalized
            )
        return normalized

    def _apply_custom_platform_settings(
        self,
        device: DeviceDefinition,
        group_vars: Dict[str, Dict[str, Any]],
    ) -> DeviceDefinition:
        """Apply custom_structured_platform_settings to device.

        Searches group_vars for custom_structured_platform_settings and applies
        matching platform-specific settings to the device.

        Parameters
        ----------
        device : DeviceDefinition
            Device to apply settings to
        group_vars : Dict[str, Dict[str, Any]]
            All group variables

        Returns
        -------
        DeviceDefinition
            Device with applied platform settings
        """
        # Search all group_vars for custom_structured_platform_settings
        for group_data in group_vars.values():
            platform_settings = group_data.get("custom_structured_platform_settings", [])

            for setting in platform_settings:
                platforms = setting.get("platforms", [])

                # Check if device platform matches
                if device.platform in platforms:
                    self.logger.debug(
                        "Applying custom platform settings for %s to device %s",
                        device.platform,
                        device.hostname,
                    )

                    # Merge custom settings into device's custom_variables
                    device.custom_variables = self._deep_merge(
                        device.custom_variables,
                        {"custom_platform_settings": setting}
                    )
                    break

        return device

    def _apply_custom_structured_configuration(
        self,
        device: DeviceDefinition,
        group_vars: Dict[str, Dict[str, Any]],
    ) -> DeviceDefinition:
        """Apply custom_structured_configuration to device.

        Merges custom_structured_configuration from group_vars into device's
        structured_config.

        Parameters
        ----------
        device : DeviceDefinition
            Device to apply configuration to
        group_vars : Dict[str, Dict[str, Any]]
            All group variables

        Returns
        -------
        DeviceDefinition
            Device with merged custom configuration
        """
        # Search all group_vars for custom_structured_configuration
        for group_data in group_vars.values():
            custom_config = group_data.get("custom_structured_configuration", {})

            if custom_config:
                self.logger.debug(
                    "Applying custom structured configuration to device %s",
                    device.hostname,
                )

                # Deep merge custom config into device's structured_config
                device.structured_config = self._deep_merge(
                    device.structured_config,
                    custom_config
                )

        return device

    def _parse_fabrics(
        self,
        global_vars: Dict[str, Any],
        group_vars: Dict[str, Dict[str, Any]],
        host_vars: Dict[str, Dict[str, Any]],
        group_hierarchy: Dict[str, List[str]],
        host_to_group: Dict[str, str],
    ) -> List[FabricDefinition]:
        """Parse loaded YAML data into fabric and device structures.

        Parameters
        ----------
        global_vars : Dict[str, Any]
            Global variables
        group_vars : Dict[str, Dict[str, Any]]
            Group variables
        host_vars : Dict[str, Dict[str, Any]]
            Host variables
        group_hierarchy : Dict[str, List[str]]
            Map of group names to their full ancestor list (sorted, handles multiple parents)
        host_to_group : Dict[str, str]
            Map of hostnames to their immediate Ansible group

        Returns
        -------
        List[FabricDefinition]
            List of parsed fabric definitions
        """
        fabrics: List[FabricDefinition] = []
        devices_by_fabric: Dict[str, List[DeviceDefinition]] = {}

        # Parse devices from group variables
        for group_name, group_data in group_vars.items():
            # Check if group defines device topology (spine, leaf, l2leaf, etc.)
            if self._is_device_topology_group(group_data):
                # Try to find fabric_name in this order:
                # 1. Current group_data
                # 2. Any other group_vars (might be parent group like campus_avd)
                # 3. Global vars
                # 4. Default to "DEFAULT"
                fabric_name = group_data.get("fabric_name")
                if not fabric_name:
                    # Search all group_vars for fabric_name
                    for other_group_data in group_vars.values():
                        if "fabric_name" in other_group_data:
                            fabric_name = other_group_data["fabric_name"]
                            break
                if not fabric_name:
                    fabric_name = global_vars.get("fabric_name", "DEFAULT")

                if fabric_name not in devices_by_fabric:
                    devices_by_fabric[fabric_name] = []

                # Parse devices from this group (pass resolved fabric_name and group_name)
                devices = self._parse_devices_from_group(
                    group_name, group_data, host_vars, global_vars, fabric_name
                )

                # Apply custom configurations and add group membership to all devices
                for i, device in enumerate(devices):
                    device = self._apply_custom_platform_settings(device, group_vars)
                    device = self._apply_custom_structured_configuration(device, group_vars)

                    # Find the actual Ansible group where this device/host is defined
                    # (e.g., IDF1, IDF2) from the pre-built host-to-group map
                    host_group = host_to_group.get(device.hostname)

                    # Collect ALL ancestor groups for proper variable inheritance
                    # A device can be in multiple group hierarchies (e.g., campus_avd AND campus_services)
                    all_ancestors: Set[str] = set()

                    # Start with the host's actual group if found, otherwise use topology group
                    effective_group = host_group if host_group and host_group in group_hierarchy else group_name

                    if effective_group in group_hierarchy:
                        # Add all ancestors of the effective group (already a list, so convert to set)
                        initial_ancestors = group_hierarchy[effective_group]
                        all_ancestors.update(initial_ancestors)

                        # For each ancestor, also add ITS ancestors (to handle multiple parent paths)
                        # Example: IDF1 has ancestor campus_leaves, which has ancestors campus_services AND campus_ports
                        # We need to collect ALL of them transitively
                        for ancestor in initial_ancestors:
                            if ancestor in group_hierarchy:
                                all_ancestors.update(group_hierarchy[ancestor])

                    # Also add ancestors of ALL intermediate groups that might have been added
                    # (e.g., if device is in IDF1, and IDF1 is under campus_leaves,
                    # and campus_leaves is under BOTH campus_avd AND campus_services,
                    # we need ancestors from both branches)
                    for existing_group in list(device.groups):
                        if existing_group in group_hierarchy:
                            all_ancestors.update(group_hierarchy[existing_group])

                    # Add all collected ancestors to device.groups (maintaining as list for compatibility)
                    for ancestor_group in sorted(all_ancestors):
                        if ancestor_group not in device.groups:
                            device.groups.append(ancestor_group)

                    devices[i] = device

                devices_by_fabric[fabric_name].extend(devices)

        # Create fabric definitions
        for fabric_name, devices in devices_by_fabric.items():
            fabric = self._create_fabric_definition(fabric_name, devices, group_vars)
            fabrics.append(fabric)

        return fabrics

    def _is_device_topology_group(self, group_data: Dict[str, Any]) -> bool:
        """Check if group data contains device topology definitions.

        Parameters
        ----------
        group_data : Dict[str, Any]
            Group variables

        Returns
        -------
        bool
            True if group contains device topology
        """
        # Check for common AVD topology keys
        topology_keys = [
            "l3spine",
            "l2leaf",
            "spine",
            "leaf",
            "type",
            "node_groups",
            "nodes",
        ]
        return any(key in group_data for key in topology_keys)

    def _parse_devices_from_group(
        self,
        group_name: str,
        group_data: Dict[str, Any],
        host_vars: Dict[str, Dict[str, Any]],
        global_vars: Dict[str, Any],
        fabric_name: str,
    ) -> List[DeviceDefinition]:
        """Parse device definitions from group data.

        Parameters
        ----------
        group_name : str
            Name of the group
        group_data : Dict[str, Any]
            Group variables
        host_vars : Dict[str, Dict[str, Any]]
            Host variables for override
        global_vars : Dict[str, Any]
            Global variables
        fabric_name : str
            Resolved fabric name (from parent resolution)

        Returns
        -------
        List[DeviceDefinition]
            List of parsed devices
        """
        devices: List[DeviceDefinition] = []
        # fabric_name is now passed as parameter, no need to resolve again

        # Determine device type from group data and normalize it
        device_type = self._normalize_device_type(
            group_data.get("type", group_name.lower())
        )

        # Parse from different AVD structures
        # NOTE: Use separate if statements (not elif) because a single file
        # can contain multiple topology types (e.g., spine: AND l3leaf:)
        if "spine" in group_data:
            # Parse spine topology
            spine_data = group_data["spine"]
            devices.extend(
                self._parse_topology_section(
                    spine_data,
                    "spine",
                    fabric_name,
                    host_vars
                )
            )

        if "l3spine" in group_data:
            devices.extend(
                self._parse_topology_section(
                    group_data["l3spine"],
                    self._normalize_device_type("l3spine"),
                    fabric_name,
                    host_vars
                )
            )

        if "leaf" in group_data:
            # Parse leaf topology
            leaf_data = group_data["leaf"]
            devices.extend(
                self._parse_topology_section(
                    leaf_data,
                    "leaf",
                    fabric_name,
                    host_vars
                )
            )

        if "l3leaf" in group_data:
            devices.extend(
                self._parse_topology_section(
                    group_data["l3leaf"],
                    self._normalize_device_type("l3leaf"),
                    fabric_name,
                    host_vars
                )
            )

        if "l2leaf" in group_data:
            devices.extend(
                self._parse_topology_section(
                    group_data["l2leaf"],
                    self._normalize_device_type("l2leaf"),
                    fabric_name,
                    host_vars
                )
            )

        # Legacy support: if no specific topology keys, check for generic structures
        if not devices:
            if "node_groups" in group_data:
                devices.extend(
                    self._parse_node_groups(
                        group_data, device_type, fabric_name, host_vars
                    )
                )
            elif "nodes" in group_data:
                # Direct node list
                for node_data in group_data.get("nodes", []):
                    device = self._parse_device_node(
                        node_data, device_type, fabric_name, host_vars
                    )
                    if device:
                        devices.append(device)

        return devices

    def _parse_topology_section(
        self,
        topology_data: Dict[str, Any],
        device_type: str,
        fabric_name: str,
        host_vars: Dict[str, Dict[str, Any]],
    ) -> List[DeviceDefinition]:
        """Parse device nodes from a topology section (spine, leaf, etc.).

        This method handles parsing of topology sections that can contain either:
        - node_groups: list of node groups
        - nodes: direct list of nodes

        Parameters
        ----------
        topology_data : Dict[str, Any]
            Topology data (e.g., spine dict or leaf dict)
        device_type : str
            Device type
        fabric_name : str
            Fabric name
        host_vars : Dict[str, Dict[str, Any]]
            Host variables

        Returns
        -------
        List[DeviceDefinition]
            List of parsed devices
        """
        devices: List[DeviceDefinition] = []

        # Check if this section has node_groups or direct nodes
        if "node_groups" in topology_data or "nodes" in topology_data:
            devices.extend(
                self._parse_node_groups(
                    topology_data, device_type, fabric_name, host_vars
                )
            )

        return devices

    def _parse_node_groups(
        self,
        topology_data: Dict[str, Any],
        device_type: str,
        fabric_name: str,
        host_vars: Dict[str, Dict[str, Any]],
    ) -> List[DeviceDefinition]:
        """Parse device nodes from node_groups structure.

        Parameters
        ----------
        topology_data : Dict[str, Any]
            Topology data containing node_groups (e.g., l3spine or l2leaf dict)
        device_type : str
            Device type
        fabric_name : str
            Fabric name
        host_vars : Dict[str, Dict[str, Any]]
            Host variables

        Returns
        -------
        List[DeviceDefinition]
            List of parsed devices
        """
        devices: List[DeviceDefinition] = []

        # Get topology-level defaults (e.g., l3spine.defaults or l2leaf.defaults)
        topology_defaults = topology_data.get("defaults", {})

        # Handle direct nodes list (e.g., spine.nodes)
        if "nodes" in topology_data and "node_groups" not in topology_data:
            for node_data in topology_data.get("nodes", []):
                # Merge topology defaults with node data
                merged_data = self._deep_merge(topology_defaults, node_data)

                device = self._parse_device_node(
                    merged_data, device_type, fabric_name, host_vars
                )
                if device:
                    devices.append(device)
            return devices

        # Handle node_groups structure (e.g., l3leaf.node_groups)
        node_groups = topology_data.get("node_groups", [])

        for node_group in node_groups:
            # Extract explicit defaults from node_group.defaults
            group_defaults = node_group.get("defaults", {})

            # All node_group fields (except 'nodes', 'defaults', 'group') are treated as defaults
            group_level_vars = {
                k: v for k, v in node_group.items()
                if k not in ("nodes", "defaults", "group")
            }

            for node_data in node_group.get("nodes", []):
                # Merge in order: topology defaults -> group-level vars -> group defaults -> node data
                merged_data = self._deep_merge(topology_defaults, {})
                merged_data = self._deep_merge(merged_data, group_level_vars)
                merged_data = self._deep_merge(merged_data, group_defaults)
                merged_data = self._deep_merge(merged_data, node_data)

                device = self._parse_device_node(
                    merged_data, device_type, fabric_name, host_vars
                )
                if device:
                    devices.append(device)

        return devices

    def _parse_device_node(
        self,
        node_data: Dict[str, Any],
        device_type: str,
        fabric_name: str,
        host_vars: Dict[str, Dict[str, Any]],
    ) -> Union[DeviceDefinition, None]:
        """Parse a single device node into DeviceDefinition.

        Parameters
        ----------
        node_data : Dict[str, Any]
            Node data
        device_type : str
            Device type
        fabric_name : str
            Fabric name
        host_vars : Dict[str, Dict[str, Any]]
            Host variables for override

        Returns
        -------
        Union[DeviceDefinition, None]
            Parsed device or None if invalid
        """
        hostname = node_data.get("name")
        if not hostname:
            return None

        # Merge with host vars if available
        if hostname in host_vars:
            node_data = self._deep_merge(node_data, host_vars[hostname])

        # Extract management IP
        mgmt_ip_str = node_data.get("mgmt_ip", node_data.get("ansible_host"))
        if not mgmt_ip_str:
            self.logger.warning("Device %s missing mgmt_ip, skipping", hostname)
            return None

        # Parse IP address (remove /24 subnet if present)
        mgmt_ip_str = str(mgmt_ip_str).split("/")[0]

        try:
            mgmt_ip = ip_address(mgmt_ip_str)
        except ValueError as e:
            self.logger.warning("Invalid mgmt_ip for %s: %s", hostname, e)
            return None

        # Extract platform
        platform = node_data.get("platform", "vEOS-lab")

        try:
            device = DeviceDefinition(
                hostname=hostname,
                platform=platform,
                mgmt_ip=mgmt_ip,
                device_type=device_type,
                fabric=fabric_name,
                pod=node_data.get("pod"),
                rack=node_data.get("rack"),
                mgmt_gateway=None,  # TODO: Parse if available
                serial_number=node_data.get("serial_number"),
                system_mac_address=node_data.get("system_mac_address"),
                structured_config=node_data.get("structured_config", {}),
                custom_variables=node_data,
            )
            return device
        except (ValueError, TypeError) as e:
            self.logger.warning("Failed to create device %s: %s", hostname, e)
            return None

    def _create_fabric_definition(
        self,
        fabric_name: str,
        devices: List[DeviceDefinition],
        group_vars: Dict[str, Dict[str, Any]],
    ) -> FabricDefinition:
        """Create a fabric definition from devices.

        Parameters
        ----------
        fabric_name : str
            Fabric name
        devices : List[DeviceDefinition]
            List of devices in fabric
        group_vars : Dict[str, Dict[str, Any]]
            Group variables

        Returns
        -------
        FabricDefinition
            Fabric definition
        """
        # Separate devices by type
        spine_devices = [d for d in devices if "spine" in d.device_type.lower()]
        leaf_devices = [
            d
            for d in devices
            if "leaf" in d.device_type.lower() and "border" not in d.device_type.lower()
        ]
        border_leaf_devices = [d for d in devices if "border" in d.device_type.lower()]

        # Determine design type from group vars
        design_type = "l3ls-evpn"  # Default
        for group_data in group_vars.values():
            if "design" in group_data and "type" in group_data["design"]:
                design_type = group_data["design"]["type"]
                break

        fabric = FabricDefinition(
            name=fabric_name,
            design_type=design_type,
            spine_devices=spine_devices,
            leaf_devices=leaf_devices,
            border_leaf_devices=border_leaf_devices,
        )

        return fabric
