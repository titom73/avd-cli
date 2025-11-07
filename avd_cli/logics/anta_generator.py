#!/usr/bin/env python
# coding: utf-8 -*-

"""ANTA test catalog generation from AVD inventory data.

This module provides comprehensive ANTA test catalog generation based on
device roles, structured configurations, and fabric topology.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from avd_cli.exceptions import TestGenerationError
from avd_cli.models.inventory import DeviceDefinition, InventoryData


class AntaCatalogGenerator:
    """Advanced ANTA test catalog generator.

    Generates comprehensive ANTA test catalogs based on AVD inventory data,
    device roles, structured configurations, and fabric topology.
    """

    def __init__(self) -> None:
        """Initialize the ANTA catalog generator."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate_catalog(
        self,
        inventory: InventoryData,
        structured_configs: Dict[str, Dict[str, Any]],
        output_path: Path,
        limit_to_groups: Optional[List[str]] = None,
    ) -> List[Path]:
        """Generate ANTA test catalog from inventory and structured configs.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data with device definitions
        structured_configs : Dict[str, Dict[str, Any]]
            Device structured configurations from pyavd
        output_path : Path
            Output directory for generated catalog
        limit_to_groups : Optional[List[str]], optional
            Groups to limit generation to, by default None

        Returns
        -------
        List[Path]
            List of generated test catalog files

        Raises
        ------
        TestGenerationError
            If catalog generation fails
        """
        self.logger.info("Generating ANTA test catalog")

        try:
            # Get devices to process
            devices = inventory.get_all_devices()
            if limit_to_groups:
                devices = [d for d in devices if d.fabric in limit_to_groups]

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            if not devices:
                self.logger.warning("No devices to process for ANTA catalog generation")
                # Create empty catalog file
                catalog_file = output_path / "anta_catalog.yaml"
                empty_catalog: Dict[str, Any] = {"anta.tests.connectivity": []}
                with open(catalog_file, "w", encoding="utf-8") as f:
                    yaml.dump(empty_catalog, f, default_flow_style=False, sort_keys=False, indent=2)
                return [catalog_file]

            # Generate individual test catalog for each device
            generated_files: List[Path] = []
            for device in devices:
                device_catalog = self._build_device_test_catalog(device, structured_configs)

                # Write device-specific catalog to file
                catalog_file = output_path / f"{device.hostname}_tests.yaml"
                with open(catalog_file, "w", encoding="utf-8") as f:
                    yaml.dump(device_catalog, f, default_flow_style=False, sort_keys=False, indent=2)

                generated_files.append(catalog_file)

            self.logger.info("Generated ANTA catalogs for %d devices", len(generated_files))
            return generated_files

        except Exception as e:
            raise TestGenerationError(f"Failed to generate ANTA catalog: {e}") from e

    def _build_test_catalog(
        self, devices: List[DeviceDefinition], structured_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build comprehensive ANTA test catalog.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices to generate tests for
        structured_configs : Dict[str, Dict[str, Any]]
            Device structured configurations

        Returns
        -------
        Dict[str, Any]
            Complete ANTA test catalog
        """
        catalog: Dict[str, Any] = {}

        # Generate connectivity tests
        catalog.update(self._generate_connectivity_tests(devices))

        # Generate BGP tests
        catalog.update(self._generate_bgp_tests(devices, structured_configs))

        # Generate EVPN tests
        catalog.update(self._generate_evpn_tests(devices, structured_configs))

        # Generate interface tests
        catalog.update(self._generate_interface_tests(devices, structured_configs))

        # Generate hardware health tests
        catalog.update(self._generate_hardware_tests(devices))

        # Generate system tests
        catalog.update(self._generate_system_tests(devices, structured_configs))

        return catalog

    def _build_device_test_catalog(
        self, device: DeviceDefinition, structured_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build ANTA test catalog for a single device.

        Parameters
        ----------
        device : DeviceDefinition
            Device to generate tests for
        structured_configs : Dict[str, Dict[str, Any]]
            Device structured configurations

        Returns
        -------
        Dict[str, Any]
            Device-specific ANTA test catalog
        """
        catalog: Dict[str, Any] = {}

        # Generate connectivity tests for this device (no peer connectivity for individual device tests)
        connectivity_tests: List[Dict[str, Any]] = []
        connectivity_tests.append(
            {
                "VerifyReachability": {
                    "hosts": [{"destination": "8.8.8.8", "source": "Management1"}]  # Test internet connectivity
                }
            }
        )
        if connectivity_tests:
            catalog["anta.tests.connectivity"] = connectivity_tests

        # Generate BGP tests for this device
        bgp_tests = self._generate_bgp_tests([device], structured_configs)
        if bgp_tests:
            catalog.update(bgp_tests)

        # Generate EVPN tests for this device
        evpn_tests = self._generate_evpn_tests([device], structured_configs)
        if evpn_tests:
            catalog.update(evpn_tests)

        # Generate interface tests for this device
        interface_tests = self._generate_interface_tests([device], structured_configs)
        if interface_tests:
            catalog.update(interface_tests)

        # Generate hardware health tests for this device
        hardware_tests = self._generate_hardware_tests([device])
        if hardware_tests:
            catalog.update(hardware_tests)

        # Generate system tests for this device
        system_tests = self._generate_system_tests([device], structured_configs)
        if system_tests:
            catalog.update(system_tests)

        return catalog

    def _generate_connectivity_tests(self, devices: List[DeviceDefinition]) -> Dict[str, Any]:
        """Generate connectivity verification tests.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices

        Returns
        -------
        Dict[str, Any]
            Connectivity test definitions
        """
        tests: List[Dict[str, Any]] = []

        # Management connectivity tests
        mgmt_ips: List[str] = [str(device.mgmt_ip) for device in devices]

        for device in devices:
            # Test reachability to all other devices' management IPs
            other_mgmt_ips: List[str] = [ip for ip in mgmt_ips if ip != str(device.mgmt_ip)]

            for target_ip in other_mgmt_ips[:5]:  # Limit to first 5 to avoid excessive tests
                tests.append({"VerifyReachability": {"hosts": [{"destination": target_ip, "source": "Management1"}]}})

        # Add loopback connectivity tests
        tests.append({"VerifyReachability": {"hosts": [{"destination": "8.8.8.8", "source": "Management1"}]}})

        return {"anta.tests.connectivity": tests} if tests else {}

    def _generate_bgp_tests(
        self, devices: List[DeviceDefinition], structured_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate BGP verification tests.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices
        structured_configs : Dict[str, Dict[str, Any]]
            Device structured configurations

        Returns
        -------
        Dict[str, Any]
            BGP test definitions
        """
        tests: List[Dict[str, Any]] = []

        for device in devices:
            config = structured_configs.get(device.hostname, {})

            # Check if device has BGP configuration
            if "router_bgp" not in config:
                continue

            bgp_config = config["router_bgp"]

            # Verify BGP is running
            tests.append({"VerifyBGPSpecificPeers": {"address_families": []}})

            # Check BGP ASN
            if "as" in bgp_config:
                tests.append({"VerifyBGPASN": {"asn": bgp_config["as"]}})

            # Check BGP peers if configured
            if "neighbors" in bgp_config:
                peer_tests: List[Dict[str, Any]] = []
                for peer_ip, peer_config in bgp_config["neighbors"].items():
                    if isinstance(peer_config, dict) and "remote_as" in peer_config:
                        peer_tests.append({"peer_address": peer_ip, "remote_asn": peer_config["remote_as"]})

                if peer_tests:
                    tests.append(
                        {
                            "VerifyBGPSpecificPeers": {
                                "address_families": [
                                    {"afi": "ipv4", "safi": "unicast", "peers": peer_tests[:10]}  # Limit to 10 peers
                                ]
                            }
                        }
                    )

        return {"anta.tests.routing.bgp": tests} if tests else {}

    def _generate_evpn_tests(
        self, devices: List[DeviceDefinition], structured_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate EVPN verification tests.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices
        structured_configs : Dict[str, Dict[str, Any]]
            Device structured configurations

        Returns
        -------
        Dict[str, Any]
            EVPN test definitions
        """
        tests: List[Dict[str, Any]] = []

        for device in devices:
            config = structured_configs.get(device.hostname, {})

            # Skip if not a leaf device (EVPN typically on leafs)
            if device.device_type not in ["leaf", "border_leaf"]:
                continue

            # Check for EVPN configuration
            router_bgp = config.get("router_bgp", {})
            if "address_family_evpn" not in router_bgp:
                continue

            # Verify EVPN peers
            evpn_config = router_bgp["address_family_evpn"]
            if "neighbors" in evpn_config:
                tests.append({"VerifyBGPEVPNCount": {"number": len(evpn_config["neighbors"])}})

            # Check for VNI configuration
            if "vlans" in config:
                vni_tests: List[int] = []
                for _, vlan_config in config["vlans"].items():
                    if isinstance(vlan_config, dict) and "vni" in vlan_config:
                        vni_tests.append(vlan_config["vni"])

                if vni_tests:
                    tests.append({"VerifyEVPNType2Route": {"vni": vni_tests[:5]}})  # Limit to 5 VNIs

        return {"anta.tests.routing.bgp": tests} if tests else {}

    def _generate_interface_tests(
        self, devices: List[DeviceDefinition], structured_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate interface status tests.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices
        structured_configs : Dict[str, Dict[str, Any]]
            Device structured configurations

        Returns
        -------
        Dict[str, Any]
            Interface test definitions
        """
        tests: List[Dict[str, Any]] = []

        for device in devices:
            config = structured_configs.get(device.hostname, {})

            # Add ethernet interface tests
            ethernet_tests = self._generate_ethernet_interface_tests(config)
            tests.extend(ethernet_tests)

            # Add loopback interface tests
            loopback_tests = self._generate_loopback_interface_tests(config)
            tests.extend(loopback_tests)

            # Add management interface test
            tests.extend(self._generate_management_interface_tests())

        return {"anta.tests.interfaces": tests} if tests else {}

    def _generate_ethernet_interface_tests(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate ethernet interface tests."""
        tests: List[Dict[str, Any]] = []

        if "ethernet_interfaces" not in config:
            return tests

        interface_names: List[str] = []
        for intf_name, intf_config in config["ethernet_interfaces"].items():
            if isinstance(intf_config, dict):
                shutdown = intf_config.get("shutdown", False)
                if not shutdown:
                    interface_names.append(intf_name)

        if interface_names:
            tests.append(
                {
                    "VerifyInterfacesStatus": {
                        "interfaces": [
                            {"name": name, "status": "up"} for name in interface_names[:20]  # Limit to 20 interfaces
                        ]
                    }
                }
            )

        return tests

    def _generate_loopback_interface_tests(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate loopback interface tests."""
        tests: List[Dict[str, Any]] = []

        if "loopback_interfaces" not in config:
            return tests

        loopback_names: List[str] = []
        for intf_name, intf_config in config["loopback_interfaces"].items():
            if isinstance(intf_config, dict):
                shutdown = intf_config.get("shutdown", False)
                if not shutdown:
                    loopback_names.append(intf_name)

        if loopback_names:
            tests.append(
                {"VerifyInterfacesStatus": {"interfaces": [{"name": name, "status": "up"} for name in loopback_names]}}
            )

        return tests

    def _generate_management_interface_tests(self) -> List[Dict[str, Any]]:
        """Generate management interface tests."""
        return [{"VerifyInterfacesStatus": {"interfaces": [{"name": "Management1", "status": "up"}]}}]

    def _generate_hardware_tests(self, devices: List[DeviceDefinition]) -> Dict[str, Any]:
        """Generate hardware health tests.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices

        Returns
        -------
        Dict[str, Any]
            Hardware test definitions
        """
        tests: List[Dict[str, Any]] = []

        # Group devices by platform for platform-specific tests
        platforms = set(device.platform for device in devices)

        for platform in platforms:
            # Generic hardware tests
            tests.extend(
                [
                    {"VerifyEnvironmentPower": {"result": "ok"}},
                    {"VerifyEnvironmentCooling": {"result": "ok"}},
                    {"VerifyTemperature": {}},
                    {"VerifyTransceiversManufacturers": {"manufacturers": ["Arista Networks", "Arastra, Inc."]}},
                ]
            )

            # Platform specific tests
            if platform.startswith("7050"):
                tests.append({"VerifyEnvironmentSystemCooling": {"result": "ok"}})
            elif platform.startswith("7280") or platform.startswith("7300"):
                tests.extend([{"VerifyEnvironmentSystemCooling": {"result": "ok"}}, {"VerifyAdverseDrops": {}}])

        return {"anta.tests.hardware": tests} if tests else {}

    def _generate_system_tests(
        self, devices: List[DeviceDefinition], structured_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate system verification tests.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices
        structured_configs : Dict[str, Dict[str, Any]]
            Device structured configurations

        Returns
        -------
        Dict[str, Any]
            System test definitions
        """
        tests: List[Dict[str, Any]] = []

        # Basic system tests
        tests.extend(
            [
                {"VerifyUptime": {"minimum": 86400}},  # 1 day minimum uptime
                {"VerifyReloadCause": {}},
                {"VerifyCoredump": {}},
                {"VerifyAgentLogs": {}},
            ]
        )

        # NTP tests if configured
        for device in devices:
            config = structured_configs.get(device.hostname, {})

            if "ntp" in config:
                ntp_config = config["ntp"]
                if "servers" in ntp_config:
                    ntp_servers: List[str] = []
                    for server_config in ntp_config["servers"]:
                        if isinstance(server_config, dict) and "name" in server_config:
                            ntp_servers.append(server_config["name"])
                        elif isinstance(server_config, str):
                            ntp_servers.append(server_config)

                    if ntp_servers:
                        tests.append({"VerifyNTP": {"servers": ntp_servers[:3]}})  # Limit to 3 servers
                break  # Only need to check NTP once

        return {"anta.tests.system": tests} if tests else {}
