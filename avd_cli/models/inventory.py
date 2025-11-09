#!/usr/bin/env python
# coding: utf-8 -*-

"""Data models for AVD inventory structures.

This module defines the core data models for representing AVD inventories,
including devices, fabrics, and complete inventory structures.
"""

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv6Address, ip_address
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from avd_cli.utils.schema import get_supported_device_types, get_supported_platforms


@dataclass
class DeviceDefinition:
    """Core device definition data model.

    Represents a single network device in the AVD inventory with all its
    properties and configuration data.

    Parameters
    ----------
    hostname : str
        Device hostname (must be valid DNS name)
    platform : str
        EOS platform type (validated against supported platforms)
    mgmt_ip : Union[IPv4Address, IPv6Address]
        Management IP address
    device_type : str
        Device role type (validated against supported types)
    fabric : str
        Fabric name this device belongs to
    groups : List[str], optional
        List of inventory groups this device belongs to, by default empty list
    pod : Optional[str], optional
        Pod identifier, by default None
    rack : Optional[str], optional
        Rack identifier, by default None
    mgmt_gateway : Optional[Union[IPv4Address, IPv6Address]], optional
        Management gateway IP, by default None
    serial_number : Optional[str], optional
        Device serial number, by default None
    system_mac_address : Optional[str], optional
        System MAC address, by default None
    structured_config : Dict[str, Any], optional
        AVD structured configuration, by default empty dict
    custom_variables : Dict[str, Any], optional
        Custom variables for this device, by default empty dict
    """

    # Required fields
    hostname: str
    platform: str
    mgmt_ip: Union[str, IPv4Address, IPv6Address]
    device_type: str
    fabric: str

    # Optional topology fields
    groups: List[str] = field(default_factory=list)
    pod: Optional[str] = None
    rack: Optional[str] = None

    # Optional network fields
    mgmt_gateway: Optional[Union[str, IPv4Address, IPv6Address]] = None
    serial_number: Optional[str] = None
    system_mac_address: Optional[str] = None

    # AVD-specific fields
    structured_config: Dict[str, Any] = field(default_factory=dict)
    custom_variables: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate device definition after initialization."""
        self._validate_hostname()
        self._validate_platform()
        self._validate_device_type()
        self._normalize_ip_addresses()

    def _validate_hostname(self) -> None:
        """Validate hostname format.

        Raises
        ------
        ValueError
            If hostname is empty or contains invalid characters
        """
        if not self.hostname:
            raise ValueError("Hostname cannot be empty")
        if not self.hostname.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid hostname format: {self.hostname}")
        if len(self.hostname) > 63:
            raise ValueError(f"Hostname too long (max 63 chars): {self.hostname}")

    def _validate_platform(self) -> None:
        """Validate platform is supported.

        Platform list is dynamically loaded from py-avd schema where possible.
        Falls back to hardcoded list if py-avd is unavailable.

        Raises
        ------
        ValueError
            If platform is not in supported platforms list
        """
        supported_platforms = get_supported_platforms()
        if self.platform not in supported_platforms:
            raise ValueError(
                f"Unsupported platform: {self.platform}. " f"Supported: {', '.join(sorted(supported_platforms))}"
            )

    def _validate_device_type(self) -> None:
        """Validate device type.

        Device type list is dynamically loaded from py-avd schema where possible.
        Falls back to hardcoded list if py-avd is unavailable.

        Raises
        ------
        ValueError
            If device_type is not in supported device types list
        """
        valid_types = get_supported_device_types()
        if self.device_type not in valid_types:
            raise ValueError(
                f"Invalid device type: {self.device_type}. " f"Valid types: {', '.join(sorted(valid_types))}"
            )

    def _normalize_ip_addresses(self) -> None:
        """Normalize IP addresses to IPv4Address or IPv6Address objects.

        Converts string IP addresses to proper IP address objects if needed.
        """
        # Convert mgmt_ip if it's a string
        if isinstance(self.mgmt_ip, str):
            self.mgmt_ip = ip_address(self.mgmt_ip)

        # Convert mgmt_gateway if it's a string
        if isinstance(self.mgmt_gateway, str):
            self.mgmt_gateway = ip_address(self.mgmt_gateway)


@dataclass
class FabricDefinition:
    """Fabric topology definition.

    Represents a complete fabric with all its devices organized by type.

    Parameters
    ----------
    name : str
        Fabric name
    design_type : str
        Design type (e.g., 'l3ls-evpn', 'mpls')
    spine_devices : List[DeviceDefinition], optional
        List of spine devices, by default empty list
    leaf_devices : List[DeviceDefinition], optional
        List of leaf devices, by default empty list
    border_leaf_devices : List[DeviceDefinition], optional
        List of border leaf devices, by default empty list
    bgp_asn_range : Optional[str], optional
        BGP ASN range for the fabric, by default None
    mlag_peer_l3_vlan : int, optional
        MLAG peer L3 VLAN ID, by default 4093
    mlag_peer_vlan : int, optional
        MLAG peer VLAN ID, by default 4094
    """

    name: str
    design_type: str
    spine_devices: List[DeviceDefinition] = field(default_factory=list)
    leaf_devices: List[DeviceDefinition] = field(default_factory=list)
    border_leaf_devices: List[DeviceDefinition] = field(default_factory=list)

    # Fabric-wide settings
    bgp_asn_range: Optional[str] = None
    mlag_peer_l3_vlan: int = 4093
    mlag_peer_vlan: int = 4094

    def get_all_devices(self) -> List[DeviceDefinition]:
        """Get all devices in fabric.

        Returns
        -------
        List[DeviceDefinition]
            Combined list of all devices in the fabric
        """
        return self.spine_devices + self.leaf_devices + self.border_leaf_devices

    def get_devices_by_type(self, device_type: str) -> List[DeviceDefinition]:
        """Get devices filtered by type.

        Parameters
        ----------
        device_type : str
            Device type to filter by

        Returns
        -------
        List[DeviceDefinition]
            List of devices matching the specified type
        """
        return [d for d in self.get_all_devices() if d.device_type == device_type]


@dataclass
class InventoryData:
    """Complete inventory data structure.

    Represents the entire AVD inventory with all fabrics and global variables.

    Parameters
    ----------
    root_path : Path
        Root path to the inventory directory
    fabrics : List[FabricDefinition], optional
        List of fabric definitions, by default empty list
    global_vars : Dict[str, Any], optional
        Global variables applicable to all devices, by default empty dict
    group_vars : Dict[str, Dict[str, Any]], optional
        Group variables (resolved from group_vars/), by default empty dict
    host_vars : Dict[str, Dict[str, Any]], optional
        Host variables (resolved from host_vars/), by default empty dict
    """

    root_path: Path
    fabrics: List[FabricDefinition] = field(default_factory=list)
    global_vars: Dict[str, Any] = field(default_factory=dict)
    group_vars: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    host_vars: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_all_devices(self) -> List[DeviceDefinition]:
        """Get all devices across all fabrics.

        Returns
        -------
        List[DeviceDefinition]
            Combined list of all devices from all fabrics
        """
        devices = []
        for fabric in self.fabrics:
            devices.extend(fabric.get_all_devices())
        return devices

    def get_device_by_hostname(self, hostname: str) -> Optional[DeviceDefinition]:
        """Find device by hostname.

        Parameters
        ----------
        hostname : str
            Hostname to search for

        Returns
        -------
        Optional[DeviceDefinition]
            Device if found, None otherwise
        """
        for device in self.get_all_devices():
            if device.hostname == hostname:
                return device
        return None

    def validate(self, skip_topology_validation: bool = False) -> List[str]:
        """Validate complete inventory structure.

        Checks for common issues like duplicate hostnames, duplicate IPs, etc.

        Parameters
        ----------
        skip_topology_validation : bool, optional
            Skip topology-specific validations (e.g., spine presence).
            Useful for cli-config workflow where structured configs are used directly,
            by default False

        Returns
        -------
        List[str]
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for duplicate hostnames
        hostnames = [d.hostname for d in self.get_all_devices()]
        duplicates = [h for h in hostnames if hostnames.count(h) > 1]
        if duplicates:
            errors.append(f"Duplicate hostnames found: {set(duplicates)}")

        # Check for duplicate management IPs
        mgmt_ips = [str(d.mgmt_ip) for d in self.get_all_devices()]
        duplicate_ips = [ip for ip in mgmt_ips if mgmt_ips.count(ip) > 1]
        if duplicate_ips:
            errors.append(f"Duplicate management IPs: {set(duplicate_ips)}")

        # Validate topology only for eos-design workflow
        if not skip_topology_validation:
            for fabric in self.fabrics:
                if not fabric.spine_devices:
                    errors.append(f"Fabric {fabric.name} has no spine devices")

        return errors
