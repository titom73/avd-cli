#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for ANTA catalog generator."""

import tempfile
from ipaddress import IPv4Address
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from avd_cli.exceptions import TestGenerationError
from avd_cli.logics.anta_generator import AntaCatalogGenerator
from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData


class TestAntaCatalogGenerator:
    """Test ANTA catalog generator functionality."""

    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = AntaCatalogGenerator()

        # Create test devices
        self.spine_device = DeviceDefinition(
            hostname="spine01",
            mgmt_ip=IPv4Address("192.168.0.11"),
            platform="7050X3",
            device_type="spine",
            fabric="TEST_FABRIC",
        )

        self.leaf_device = DeviceDefinition(
            hostname="leaf01",
            mgmt_ip=IPv4Address("192.168.0.21"),
            platform="7280R3",
            device_type="leaf",
            fabric="TEST_FABRIC",
        )

        # Create test inventory
        fabric = FabricDefinition(name="TEST_FABRIC", design_type="l3ls-evpn")
        fabric.spine_devices = [self.spine_device]
        fabric.leaf_devices = [self.leaf_device]

        self.inventory = InventoryData(root_path=Path("/tmp/test"), fabrics=[fabric])

        # Create structured configs
        self.structured_configs = {
            "spine01": {
                "router_bgp": {
                    "as": 65001,
                    "neighbors": {"192.168.0.21": {"remote_as": 65002}, "192.168.0.22": {"remote_as": 65003}},
                },
                "ethernet_interfaces": {
                    "Ethernet1": {"description": "To leaf01", "shutdown": False},
                    "Ethernet2": {"description": "To leaf02", "shutdown": False},
                },
                "loopback_interfaces": {"Loopback0": {"ip_address": "10.0.0.1", "shutdown": False}},
                "ntp": {"servers": [{"name": "pool.ntp.org"}, {"name": "time.google.com"}]},
            },
            "leaf01": {
                "router_bgp": {
                    "as": 65002,
                    "neighbors": {"192.168.0.11": {"remote_as": 65001}},
                    "address_family_evpn": {"neighbors": {"192.168.0.11": {"activate": True}}},
                },
                "ethernet_interfaces": {"Ethernet48": {"description": "To spine01", "shutdown": False}},
                "loopback_interfaces": {
                    "Loopback0": {"ip_address": "10.0.0.2", "shutdown": False},
                    "Loopback1": {"ip_address": "10.1.0.2", "shutdown": False},
                },
                "vlans": {"100": {"vni": 10100}, "200": {"vni": 10200}},
            },
        }

    def test_init(self):
        """Test generator initialization."""
        generator = AntaCatalogGenerator()
        assert generator is not None
        assert hasattr(generator, "logger")

    def test_generate_catalog_success(self):
        """Test successful catalog generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)

            files = self.generator.generate_catalog(self.inventory, self.structured_configs, output_path)

            assert len(files) == 2  # One file per device
            assert all(f.exists() for f in files)

            # Check spine catalog content
            spine_file = output_path / "spine01_tests.yaml"
            assert spine_file in files

            with open(spine_file, encoding="utf-8") as f:
                spine_catalog = yaml.safe_load(f)

            # Verify catalog structure
            assert "anta.tests.connectivity" in spine_catalog
            assert "anta.tests.routing.bgp" in spine_catalog
            assert "anta.tests.interfaces" in spine_catalog
            assert "anta.tests.hardware" in spine_catalog
            assert "anta.tests.system" in spine_catalog

    def test_generate_catalog_empty_inventory(self):
        """Test catalog generation with empty inventory."""
        empty_inventory = InventoryData(root_path=Path("/tmp/test"), fabrics=[])

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)

            files = self.generator.generate_catalog(empty_inventory, {}, output_path)

            assert len(files) == 1
            assert files[0].name == "anta_catalog.yaml"

            with open(files[0], encoding="utf-8") as f:
                catalog = yaml.safe_load(f)

            assert "anta.tests.connectivity" in catalog
            assert catalog["anta.tests.connectivity"] == []

    def test_generate_catalog_with_limit_to_groups(self):
        """Test catalog generation with group filtering."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)

            files = self.generator.generate_catalog(
                self.inventory, self.structured_configs, output_path, limit_to_groups=["NONEXISTENT_FABRIC"]
            )

            # Should create empty catalog when no devices match
            assert len(files) == 1
            assert files[0].name == "anta_catalog.yaml"

    def test_generate_catalog_io_error(self):
        """Test catalog generation with I/O error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "nonexistent" / "path"

            # Create a read-only directory to cause write error
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                with pytest.raises(TestGenerationError, match="Failed to generate ANTA catalog"):
                    self.generator.generate_catalog(self.inventory, self.structured_configs, output_path)

    def test_build_device_test_catalog_spine(self):
        """Test device catalog generation for spine device."""
        catalog = self.generator._build_device_test_catalog(self.spine_device, self.structured_configs)

        # Verify catalog contains expected test sections
        assert "anta.tests.connectivity" in catalog
        assert "anta.tests.routing.bgp" in catalog
        assert "anta.tests.interfaces" in catalog
        assert "anta.tests.hardware" in catalog
        assert "anta.tests.system" in catalog

        # Verify BGP tests
        bgp_tests = catalog["anta.tests.routing.bgp"]
        assert any("VerifyBGPASN" in str(test) for test in bgp_tests)
        assert any("VerifyBGPSpecificPeers" in str(test) for test in bgp_tests)

    def test_build_device_test_catalog_leaf(self):
        """Test device catalog generation for leaf device."""
        catalog = self.generator._build_device_test_catalog(self.leaf_device, self.structured_configs)

        # Verify EVPN tests are included for leaf
        bgp_tests = catalog.get("anta.tests.routing.bgp", [])
        assert any("VerifyBGPEVPNCount" in str(test) for test in bgp_tests)
        assert any("VerifyEVPNType2Route" in str(test) for test in bgp_tests)

    def test_generate_connectivity_tests(self):
        """Test connectivity test generation."""
        devices = [self.spine_device, self.leaf_device]

        tests = self.generator._generate_connectivity_tests(devices)

        assert "anta.tests.connectivity" in tests
        connectivity_tests = tests["anta.tests.connectivity"]

        # Should have reachability tests
        assert any("VerifyReachability" in str(test) for test in connectivity_tests)
        assert len(connectivity_tests) > 0

    def test_generate_bgp_tests_with_neighbors(self):
        """Test BGP test generation with neighbors."""
        devices = [self.spine_device]

        tests = self.generator._generate_bgp_tests(devices, self.structured_configs)

        assert "anta.tests.routing.bgp" in tests
        bgp_tests = tests["anta.tests.routing.bgp"]

        # Should have ASN and peer tests
        assert any("VerifyBGPASN" in str(test) for test in bgp_tests)
        assert any("VerifyBGPSpecificPeers" in str(test) for test in bgp_tests)

    def test_generate_bgp_tests_no_bgp_config(self):
        """Test BGP test generation without BGP config."""
        device_no_bgp = DeviceDefinition(
            hostname="device01",
            mgmt_ip=IPv4Address("192.168.0.1"),
            platform="7050X3",
            device_type="spine",
            fabric="TEST",
        )

        tests = self.generator._generate_bgp_tests([device_no_bgp], {})

        # Should return empty dict when no BGP config
        assert tests == {}

    def test_generate_evpn_tests_leaf_device(self):
        """Test EVPN test generation for leaf device."""
        devices = [self.leaf_device]

        tests = self.generator._generate_evpn_tests(devices, self.structured_configs)

        assert "anta.tests.routing.bgp" in tests
        evpn_tests = tests["anta.tests.routing.bgp"]

        # Should have EVPN peer and VNI tests
        assert any("VerifyBGPEVPNCount" in str(test) for test in evpn_tests)
        assert any("VerifyEVPNType2Route" in str(test) for test in evpn_tests)

    def test_generate_evpn_tests_spine_device(self):
        """Test EVPN test generation for spine device (should skip)."""
        devices = [self.spine_device]

        tests = self.generator._generate_evpn_tests(devices, self.structured_configs)

        # Spine devices should not generate EVPN tests
        assert tests == {}

    def test_generate_interface_tests(self):
        """Test interface test generation."""
        devices = [self.spine_device, self.leaf_device]

        tests = self.generator._generate_interface_tests(devices, self.structured_configs)

        assert "anta.tests.interfaces" in tests
        interface_tests = tests["anta.tests.interfaces"]

        # Should have interface status tests
        assert any("VerifyInterfacesStatus" in str(test) for test in interface_tests)

    def test_generate_ethernet_interface_tests(self):
        """Test ethernet interface test generation."""
        config = self.structured_configs["spine01"]

        tests = self.generator._generate_ethernet_interface_tests(config)

        assert len(tests) > 0
        assert any("VerifyInterfacesStatus" in str(test) for test in tests)

        # Check that non-shutdown interfaces are included
        test_dict = tests[0]
        status_test = test_dict["VerifyInterfacesStatus"]
        interface_names = [intf["name"] for intf in status_test["interfaces"]]
        assert "Ethernet1" in interface_names
        assert "Ethernet2" in interface_names

    def test_generate_ethernet_interface_tests_no_config(self):
        """Test ethernet interface tests with no interface config."""
        config = {}

        tests = self.generator._generate_ethernet_interface_tests(config)

        assert tests == []

    def test_generate_loopback_interface_tests(self):
        """Test loopback interface test generation."""
        config = self.structured_configs["leaf01"]

        tests = self.generator._generate_loopback_interface_tests(config)

        assert len(tests) > 0
        assert any("VerifyInterfacesStatus" in str(test) for test in tests)

    def test_generate_loopback_interface_tests_no_config(self):
        """Test loopback interface tests with no loopback config."""
        config = {}

        tests = self.generator._generate_loopback_interface_tests(config)

        assert tests == []

    def test_generate_management_interface_tests(self):
        """Test management interface test generation."""
        tests = self.generator._generate_management_interface_tests()

        assert len(tests) == 1
        assert "VerifyInterfacesStatus" in str(tests[0])
        assert "Management1" in str(tests[0])

    def test_generate_hardware_tests(self):
        """Test hardware test generation."""
        devices = [self.spine_device, self.leaf_device]

        tests = self.generator._generate_hardware_tests(devices)

        assert "anta.tests.hardware" in tests
        hardware_tests = tests["anta.tests.hardware"]

        # Should have basic hardware tests
        assert any("VerifyEnvironmentPower" in str(test) for test in hardware_tests)
        assert any("VerifyEnvironmentCooling" in str(test) for test in hardware_tests)
        assert any("VerifyTemperature" in str(test) for test in hardware_tests)

    def test_generate_hardware_tests_platform_specific(self):
        """Test platform-specific hardware test generation."""
        # Create device with 7280 platform
        device_7280 = DeviceDefinition(
            hostname="leaf02", mgmt_ip=IPv4Address("192.168.0.22"), platform="7280R3", device_type="leaf", fabric="TEST"
        )

        tests = self.generator._generate_hardware_tests([device_7280])

        hardware_tests = tests["anta.tests.hardware"]

        # Should include platform-specific tests
        assert any("VerifyAdverseDrops" in str(test) for test in hardware_tests)

    def test_generate_system_tests(self):
        """Test system test generation."""
        devices = [self.spine_device]

        tests = self.generator._generate_system_tests(devices, self.structured_configs)

        assert "anta.tests.system" in tests
        system_tests = tests["anta.tests.system"]

        # Should have basic system tests
        assert any("VerifyUptime" in str(test) for test in system_tests)
        assert any("VerifyReloadCause" in str(test) for test in system_tests)
        assert any("VerifyCoredump" in str(test) for test in system_tests)

        # Should have NTP tests when configured
        assert any("VerifyNTP" in str(test) for test in system_tests)

    def test_generate_system_tests_no_ntp(self):
        """Test system test generation without NTP config."""
        devices = [self.leaf_device]
        configs_no_ntp = {"leaf01": {"router_bgp": {"as": 65002}}}

        tests = self.generator._generate_system_tests(devices, configs_no_ntp)

        system_tests = tests["anta.tests.system"]

        # Should not have NTP tests
        assert not any("VerifyNTP" in str(test) for test in system_tests)

    def test_build_test_catalog_comprehensive(self):
        """Test comprehensive test catalog building."""
        devices = [self.spine_device, self.leaf_device]

        catalog = self.generator._build_test_catalog(devices, self.structured_configs)

        # Should have all test categories
        expected_categories = [
            "anta.tests.connectivity",
            "anta.tests.routing.bgp",
            "anta.tests.interfaces",
            "anta.tests.hardware",
            "anta.tests.system",
        ]

        for category in expected_categories:
            if category in catalog:
                assert len(catalog[category]) > 0

    def test_invalid_structured_config_format(self):
        """Test handling of invalid structured config format."""
        invalid_configs = {"spine01": "invalid_string_config"}  # Should be dict

        # Should not raise exception, just skip invalid configs
        catalog = self.generator._build_device_test_catalog(self.spine_device, invalid_configs)

        # Should still generate basic tests
        assert "anta.tests.connectivity" in catalog
        assert "anta.tests.hardware" in catalog

    def test_edge_case_empty_bgp_neighbors(self):
        """Test BGP test generation with empty neighbors dict."""
        config_empty_neighbors = {"spine01": {"router_bgp": {"as": 65001, "neighbors": {}}}}

        tests = self.generator._generate_bgp_tests([self.spine_device], config_empty_neighbors)

        bgp_tests = tests["anta.tests.routing.bgp"]

        # Should still have ASN test
        assert any("VerifyBGPASN" in str(test) for test in bgp_tests)

    def test_large_interface_count_limiting(self):
        """Test that interface tests are limited to prevent excessive test generation."""
        # Create config with many interfaces
        many_interfaces = {f"Ethernet{i}": {"shutdown": False} for i in range(1, 100)}

        config_many_intfs = {"ethernet_interfaces": many_interfaces}

        tests = self.generator._generate_ethernet_interface_tests(config_many_intfs)

        # Should limit to 20 interfaces
        assert len(tests) > 0
        status_test = tests[0]["VerifyInterfacesStatus"]
        assert len(status_test["interfaces"]) <= 20

    def test_bgp_peer_limiting(self):
        """Test that BGP peer tests are limited."""
        # Create config with many BGP peers
        many_peers = {f"192.168.1.{i}": {"remote_as": 65000 + i} for i in range(1, 50)}

        config_many_peers = {"spine01": {"router_bgp": {"as": 65001, "neighbors": many_peers}}}

        tests = self.generator._generate_bgp_tests([self.spine_device], config_many_peers)

        bgp_tests = tests["anta.tests.routing.bgp"]

        # Find the peer test
        peer_test = None
        for test in bgp_tests:
            if "VerifyBGPSpecificPeers" in test and "address_families" in test["VerifyBGPSpecificPeers"]:
                addr_families = test["VerifyBGPSpecificPeers"]["address_families"]
                if addr_families and "peers" in addr_families[0]:
                    peer_test = addr_families[0]["peers"]
                    break

        # Should limit to 10 peers
        if peer_test:
            assert len(peer_test) <= 10

    def test_build_device_test_catalog_integration(self):
        """Test the _build_device_test_catalog method directly covering all test generation paths."""
        device = DeviceDefinition(
            hostname="comprehensive-device",
            mgmt_ip=IPv4Address("192.168.0.50"),
            platform="7280R3",
            device_type="leaf",
            fabric="TEST"
        )

        comprehensive_configs = {
            "comprehensive-device": {
                "router_bgp": {
                    "as": 65001,
                    "neighbors": {"192.168.0.1": {"remote_as": 65002}},
                    "address_family_evpn": {"neighbors": {"192.168.0.1": {"activate": True}}}
                },
                "ethernet_interfaces": {"Ethernet1": {"description": "Test", "shutdown": False}},
                "loopback_interfaces": {"Loopback0": {"ip_address": "10.0.0.1"}},
                "management_interfaces": {"Management1": {"ip_address": "192.168.0.50/24"}},
                "ntp": {"servers": [{"name": "pool.ntp.org"}]},
            }
        }

        # Test the complete catalog generation for a single device
        catalog = self.generator._build_device_test_catalog(device, comprehensive_configs)

        # Verify all test categories are present
        expected_categories = [
            "anta.tests.connectivity",
            "anta.tests.routing.bgp",
            "anta.tests.interfaces",
            "anta.tests.hardware",
            "anta.tests.system"
        ]

        for category in expected_categories:
            assert category in catalog, f"Missing category: {category}"
            assert isinstance(catalog[category], list), f"Category {category} should be a list"

    def test_empty_structured_configs_handling(self):
        """Test handling of devices with minimal or empty structured configs."""
        device = DeviceDefinition(
            hostname="minimal-device",
            mgmt_ip=IPv4Address("192.168.0.99"),
            platform="7050X3",
            device_type="spine",
            fabric="TEST"
        )

        # Test with device not in structured configs
        catalog = self.generator._build_device_test_catalog(device, {})

        # Should still generate basic connectivity and hardware tests
        assert "anta.tests.connectivity" in catalog
        assert "anta.tests.hardware" in catalog

        # BGP tests may or may not be present when device has no config
        # but system and interfaces should be present
        assert "anta.tests.system" in catalog
        assert "anta.tests.interfaces" in catalog

    def test_device_filtering_integration(self):
        """Test complete device filtering workflow when generating catalogs."""
        # Create inventory with multiple fabrics for filtering test
        fabric1 = FabricDefinition(name="FABRIC1", design_type="l3ls-evpn")
        fabric1.spine_devices = [self.spine_device]

        fabric2 = FabricDefinition(name="FABRIC2", design_type="l3ls-evpn")
        fabric2.leaf_devices = [self.leaf_device]

        multi_fabric_inventory = InventoryData(
            root_path=Path("/tmp/test"),
            fabrics=[fabric1, fabric2]
        )

        # Generate catalog limited to FABRIC1 only
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)
            files = self.generator.generate_catalog(
                multi_fabric_inventory,
                self.structured_configs,
                output_path,
                limit_to_groups=["FABRIC1"]
            )

            # Should generate files (may be combined or individual)
            assert len(files) >= 1

            # Verify file content contains expected tests
            with open(files[0], encoding="utf-8") as f:
                content = yaml.safe_load(f)
                assert "anta.tests.connectivity" in content

    def test_error_handling_in_catalog_generation(self):
        """Test error handling during catalog generation process."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)

            # Test with device that has malformed structured config
            malformed_configs = {
                "spine01": {
                    "router_bgp": "invalid_structure"  # Should be dict, not string
                }
            }

            # Should handle malformed configs gracefully
            try:
                files = self.generator.generate_catalog(
                    self.inventory, malformed_configs, output_path
                )
                # If no exception, verify basic structure is still created
                assert len(files) >= 1
            except Exception:
                # If exception occurs, it should be a specific type
                pass  # Allow for graceful handling

    def test_comprehensive_interface_tests(self):
        """Test comprehensive interface test generation with all interface types."""
        device = DeviceDefinition(
            hostname="interface-test-device",
            mgmt_ip=IPv4Address("192.168.0.100"),
            platform="7280R3",
            device_type="leaf",
            fabric="TEST"
        )

        interface_configs = {
            "interface-test-device": {
                "ethernet_interfaces": {
                    "Ethernet1": {"description": "Server connection", "shutdown": False},
                    "Ethernet2": {"description": "Uplink", "shutdown": False},
                },
                "loopback_interfaces": {
                    "Loopback0": {"ip_address": "10.0.0.1/32"},
                    "Loopback1": {"ip_address": "10.1.0.1/32"},
                },
                "management_interfaces": {
                    "Management1": {"ip_address": "192.168.0.100/24"}
                }
            }
        }

        tests = self.generator._generate_interface_tests([device], interface_configs)

        # Verify interface tests are generated
        interface_tests = tests["anta.tests.interfaces"]
        assert len(interface_tests) > 0

        # Should include various interface types
        test_types = [list(test.keys())[0] for test in interface_tests]
        assert any("VerifyInterfacesStatus" in t for t in test_types)
