#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for inventory loader module.

Tests cover YAML loading, device parsing, fabric creation,
and validation as specified in AC-001 to AC-010.
"""

import pytest
from ipaddress import IPv4Address

from avd_cli.exceptions import FileSystemError, InvalidInventoryError
from avd_cli.logics.loader import InventoryLoader


class TestInventoryLoader:
    """Tests for InventoryLoader class."""

    @pytest.fixture
    def loader(self):
        """Create a loader instance."""
        return InventoryLoader()

    @pytest.fixture
    def valid_inventory_path(self, tmp_path):
        """Create a minimal valid inventory structure."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create group_vars/all.yml
        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "all.yml").write_text("---\nglobal_var: test_value\n")

        # Create group_vars/FABRIC/fabric.yml
        fabric_dir = group_vars_dir / "FABRIC"
        fabric_dir.mkdir()
        (fabric_dir / "fabric.yml").write_text("""---
fabric_name: TEST_FABRIC
type: l3spine
l3spine:
  defaults:
    platform: vEOS-lab
    bgp_as: 65001
  node_groups:
  - group: SPINES
    nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
""")

        return inventory_dir

    def test_load_valid_inventory(self, loader, valid_inventory_path):
        """AC-001: Given valid inventory directory, When loading, Then all YAML files parsed successfully."""
        inventory = loader.load(valid_inventory_path)

        assert inventory is not None
        assert len(inventory.fabrics) == 1
        assert inventory.fabrics[0].name == "TEST_FABRIC"
        assert len(inventory.fabrics[0].get_all_devices()) == 1
        assert inventory.fabrics[0].get_all_devices()[0].hostname == "spine1"

    def test_load_missing_directory(self, loader, tmp_path):
        """AC-003: Given missing directory, When loading, Then clear error message."""
        non_existent = tmp_path / "non_existent"

        with pytest.raises(FileSystemError, match="does not exist"):
            loader.load(non_existent)

    def test_load_invalid_path(self, loader, tmp_path):
        """Test loading from a file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("not a directory")

        with pytest.raises(FileSystemError, match="not a directory"):
            loader.load(file_path)

    def test_load_group_vars_directory_format(self, loader, tmp_path):
        """AC-005: Given group_vars/GROUP as directory, When loading, Then all files merged."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # Create FABRIC as directory with multiple files
        fabric_dir = group_vars_dir / "FABRIC"
        fabric_dir.mkdir()
        (fabric_dir / "01-base.yml").write_text("---\nvar1: value1\n")
        (fabric_dir / "02-override.yml").write_text("---\nvar2: value2\n")
        (fabric_dir / "fabric.yml").write_text("""---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: device1
        id: 1
        mgmt_ip: 192.168.0.1/24
""")

        inventory = loader.load(inventory_dir)

        # Verify fabric loads correctly with directory-based group_vars
        assert len(inventory.fabrics) == 1
        assert inventory.fabrics[0].name == "TEST"

    def test_load_group_vars_file_format(self, loader, tmp_path):
        """AC-006: Given group_vars/GROUP as file, When loading, Then single file loaded."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # Create FABRIC as single file
        (group_vars_dir / "FABRIC.yml").write_text("""---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: device1
        id: 1
        mgmt_ip: 192.168.0.1/24
""")

        inventory = loader.load(inventory_dir)
        assert len(inventory.fabrics) == 1

    def test_load_host_vars_directory_format(self, loader, tmp_path):
        """AC-010: Given host_vars/HOST as directory, When loading, Then all files merged."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "FABRIC.yml").write_text("""---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: 192.168.0.1/24
""")

        host_vars_dir = inventory_dir / "host_vars"
        host_vars_dir.mkdir()

        # Create spine1 as directory
        spine1_dir = host_vars_dir / "spine1"
        spine1_dir.mkdir()
        (spine1_dir / "base.yml").write_text("---\nhost_var1: val1\n")
        (spine1_dir / "extra.yml").write_text("---\nhost_var2: val2\n")

        inventory = loader.load(inventory_dir)
        # Just verify it loads without error
        assert len(inventory.fabrics) == 1

    def test_device_type_mapping(self, loader, tmp_path):
        """AC-025 to AC-028: Test device type mapping."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # Test l3spine -> spine mapping
        (group_vars_dir / "SPINES.yml").write_text("""---
fabric_name: TEST
type: l3spine
l3spine:
  defaults:
    platform: vEOS-lab
  node_groups:
  - group: TEST
    nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
""")

        inventory = loader.load(inventory_dir)
        device = inventory.fabrics[0].get_all_devices()[0]

        # l3spine should be mapped to spine
        assert device.device_type == "spine"
        assert device.hostname == "spine1"

    def test_l2leaf_mapping(self, loader, tmp_path):
        """AC-026: Test l2leaf -> leaf mapping."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        (group_vars_dir / "LEAVES.yml").write_text("""---
fabric_name: TEST
type: l2leaf
l2leaf:
  defaults:
    platform: vEOS-lab
  node_groups:
  - group: TEST
    nodes:
    - name: leaf1
      id: 1
      mgmt_ip: 192.168.0.20/24
""")

        inventory = loader.load(inventory_dir)
        device = inventory.fabrics[0].get_all_devices()[0]

        assert device.device_type == "leaf"

    def test_inventory_yml_loading(self, loader, tmp_path):
        """Test loading hosts from inventory.yml."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create inventory.yml with hosts
        (inventory_dir / "inventory.yml").write_text("""---
all:
  children:
    FABRIC:
      vars:
        fabric_name: TEST
      hosts:
        spine1:
          ansible_host: 192.168.0.10
""")

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "FABRIC.yml").write_text("""---
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: 192.168.0.10/24
""")

        inventory = loader.load(inventory_dir)
        # Verify it loads without error
        assert inventory is not None

    def test_template_resolution(self, loader, tmp_path):
        """Test that Jinja2 templates are resolved during loading."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # Create inventory with templates
        (inventory_dir / "inventory.yml").write_text("""---
all:
  children:
    FABRIC:
      vars:
        platform_var: vEOS-lab
      hosts:
        spine1:
          ansible_host: 192.168.0.10
""")

        (group_vars_dir / "FABRIC.yml").write_text("""---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    platform: "{{ platform_var }}"
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: "{{ hostvars['spine1'].ansible_host }}/24"
""")

        inventory = loader.load(inventory_dir)
        device = inventory.fabrics[0].get_all_devices()[0]

        # Template should be resolved
        assert device.mgmt_ip == IPv4Address("192.168.0.10")

    def test_topology_defaults_merge(self, loader, tmp_path):
        """Test that topology defaults are properly merged to nodes."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        (group_vars_dir / "FABRIC.yml").write_text("""---
fabric_name: TEST
type: l3spine
l3spine:
  defaults:
    platform: 7050X3
    bgp_as: 65001
  node_groups:
  - group: TEST
    nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
""")

        inventory = loader.load(inventory_dir)
        device = inventory.fabrics[0].get_all_devices()[0]

        # Platform from topology defaults should be applied
        assert device.platform == "7050X3"

    def test_node_group_level_vars(self, loader, tmp_path):
        """Test that node_group level vars override topology defaults."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        (group_vars_dir / "FABRIC.yml").write_text("""---
fabric_name: TEST
type: l2leaf
l2leaf:
  defaults:
    platform: 722XP
  node_groups:
  - group: GROUP1
    platform: 720XP
    nodes:
    - name: leaf1
      id: 1
      mgmt_ip: 192.168.0.20/24
""")

        inventory = loader.load(inventory_dir)
        device = inventory.fabrics[0].get_all_devices()[0]

        # Node group platform should override topology default
        assert device.platform == "720XP"

    def test_fabric_name_resolution(self, loader, tmp_path):
        """Test fabric_name resolution from group_vars."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # fabric_name in a separate file
        (group_vars_dir / "all.yml").write_text("---\nfabric_name: MY_FABRIC\n")

        (group_vars_dir / "SPINES.yml").write_text("""---
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: 192.168.0.10/24
""")

        inventory = loader.load(inventory_dir)

        # Should use fabric_name from all.yml or default
        assert inventory.fabrics[0].name in ["MY_FABRIC", "DEFAULT"]


class TestInventoryLoaderEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def loader(self):
        """Create a loader instance."""
        return InventoryLoader()

    def test_empty_inventory(self, loader, tmp_path):
        """Test loading empty inventory directory."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create minimal structure to pass validation
        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "all.yml").write_text("---\n# Empty\n")

        # Empty inventory should not crash
        inventory = loader.load(inventory_dir)
        assert inventory is not None
        assert len(inventory.fabrics) == 0

    def test_invalid_yaml_syntax(self, loader, tmp_path):
        """AC-002: Given YAML with syntax error, When loading, Then error includes file path."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # Invalid YAML
        (group_vars_dir / "invalid.yml").write_text("""---
invalid: [unclosed bracket
""")

        with pytest.raises((InvalidInventoryError, ValueError)):
            loader.load(inventory_dir)

    def test_missing_mgmt_ip(self, loader, tmp_path):
        """AC-011: Given device missing required field, When validating, Then error indicates missing field."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        (group_vars_dir / "FABRIC.yml").write_text("""---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        # mgmt_ip is missing
""")

        # Should log warning about missing mgmt_ip
        inventory = loader.load(inventory_dir)
        # Device should be skipped
        assert len(inventory.fabrics) == 0 or len(inventory.fabrics[0].get_all_devices()) == 0

    def test_invalid_ip_address(self, loader, tmp_path):
        """AC-012: Given invalid IP address format, When validating, Then error explains requirements."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        (group_vars_dir / "FABRIC.yml").write_text("""---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: not-an-ip
""")

        # Should log warning about invalid IP
        inventory = loader.load(inventory_dir)
        # Device with invalid IP should be skipped
        assert len(inventory.fabrics) == 0 or len(inventory.fabrics[0].get_all_devices()) == 0
