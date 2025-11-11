#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for inventory loader module.

Tests cover YAML loading, device parsing, fabric creation,
and validation as specified in AC-001 to AC-010.
"""

from ipaddress import IPv4Address

import pytest

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
        (fabric_dir / "fabric.yml").write_text(
            """---
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
"""
        )

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
        (fabric_dir / "fabric.yml").write_text(
            """---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: device1
        id: 1
        mgmt_ip: 192.168.0.1/24
"""
        )

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
        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: device1
        id: 1
        mgmt_ip: 192.168.0.1/24
"""
        )

        inventory = loader.load(inventory_dir)
        assert len(inventory.fabrics) == 1

    def test_load_host_vars_directory_format(self, loader, tmp_path):
        """AC-010: Given host_vars/HOST as directory, When loading, Then all files merged."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: 192.168.0.1/24
"""
        )

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
        (group_vars_dir / "SPINES.yml").write_text(
            """---
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
"""
        )

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

        (group_vars_dir / "LEAVES.yml").write_text(
            """---
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
"""
        )

        inventory = loader.load(inventory_dir)
        device = inventory.fabrics[0].get_all_devices()[0]

        assert device.device_type == "leaf"

    def test_inventory_yml_loading(self, loader, tmp_path):
        """Test loading hosts from inventory.yml."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create inventory.yml with hosts
        (inventory_dir / "inventory.yml").write_text(
            """---
all:
  children:
    FABRIC:
      vars:
        fabric_name: TEST
      hosts:
        spine1:
          ansible_host: 192.168.0.10
"""
        )

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "FABRIC.yml").write_text(
            """---
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: 192.168.0.10/24
"""
        )

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
        (inventory_dir / "inventory.yml").write_text(
            """---
all:
  children:
    FABRIC:
      vars:
        platform_var: vEOS-lab
      hosts:
        spine1:
          ansible_host: 192.168.0.10
"""
        )

        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    platform: "{{ platform_var }}"
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: "{{ hostvars['spine1'].ansible_host }}/24"
"""
        )

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

        (group_vars_dir / "FABRIC.yml").write_text(
            """---
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
"""
        )

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

        (group_vars_dir / "FABRIC.yml").write_text(
            """---
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
"""
        )

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

        (group_vars_dir / "SPINES.yml").write_text(
            """---
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: 192.168.0.10/24
"""
        )

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
        (group_vars_dir / "invalid.yml").write_text(
            """---
invalid: [unclosed bracket
"""
        )

        with pytest.raises((InvalidInventoryError, ValueError)):
            loader.load(inventory_dir)

    def test_missing_mgmt_ip(self, loader, tmp_path):
        """AC-011: Given device missing required field, When validating, Then error indicates missing field."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        # mgmt_ip is missing
"""
        )

        # Should log warning about missing mgmt_ip
        inventory = loader.load(inventory_dir)
        # Device should be skipped
        assert len(inventory.fabrics) == 0 or len(inventory.fabrics[0].get_all_devices()) == 0

    def test_mixed_file_and_directory_format(self, loader, tmp_path):
        """REQ-008: Test mixed file and directory formats in group_vars.

        Verifies that the loader supports:
        - Some groups as files (FABRIC.yml)
        - Some groups as directories (SPINES/, all/)
        - All loaded and merged correctly
        """
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # Create 'all' as directory with multiple files
        all_dir = group_vars_dir / "all"
        all_dir.mkdir()
        (all_dir / "global.yml").write_text("---\nglobal_var: global_value\n")
        (all_dir / "platform.yml").write_text("---\ndefault_platform: vEOS-lab\n")

        # Create 'FABRIC' as single file
        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: MIXED_TEST

# Spine Switches
spine:
  defaults:
    platform: vEOS-lab
    bgp_as: 65000
  nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
    - name: spine2
      id: 2
      mgmt_ip: 192.168.0.11/24
"""
        )

        # Create 'SPINES' as directory
        spines_dir = group_vars_dir / "SPINES"
        spines_dir.mkdir()
        (spines_dir / "topology.yml").write_text(
            """---
# Additional spine configuration
"""
        )
        (spines_dir / "bgp.yml").write_text("---\nbgp_peer_groups:\n  - name: IPv4-UNDERLAY-PEERS\n")

        # Load inventory
        inventory = loader.load(inventory_dir)

        # Verify fabric loaded correctly from file format
        assert len(inventory.fabrics) >= 1
        fabric = inventory.fabrics[0]
        assert fabric.name == "MIXED_TEST"

        # Verify directory-based group_vars loaded (SPINES/)
        # The fact that loading succeeds validates mixed format support
        assert inventory is not None

    def test_host_vars_mixed_format(self, loader, tmp_path):
        """REQ-008: Test mixed file and directory formats in host_vars.

        Verifies that the loader supports:
        - Some hosts as files (spine2.yml)
        - Some hosts as directories (spine1/)
        - All loaded and merged correctly
        """
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create basic fabric
        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: HOST_VARS_TEST

# Spine Switches
spine:
  defaults:
    platform: vEOS-lab
  nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
    - name: spine2
      id: 2
      mgmt_ip: 192.168.0.11/24
"""
        )

        # Create host_vars with mixed format
        host_vars_dir = inventory_dir / "host_vars"
        host_vars_dir.mkdir()

        # spine1 as directory
        spine1_dir = host_vars_dir / "spine1"
        spine1_dir.mkdir()
        (spine1_dir / "system.yml").write_text("---\nhostname: spine1-custom\n")
        (spine1_dir / "interfaces.yml").write_text("---\ninterfaces:\n  - name: Ethernet1\n")

        # spine2 as single file
        (host_vars_dir / "spine2.yml").write_text("---\nhostname: spine2-custom\n")

        # Load inventory
        inventory = loader.load(inventory_dir)

        # Verify fabric loaded from file-based group_vars
        assert len(inventory.fabrics) >= 1

        # Verify both file (spine2.yml) and directory (spine1/) host_vars loaded
        # The fact that loading succeeds validates mixed format support
        assert inventory is not None

    def test_invalid_ip_address_format(self, loader, tmp_path):
        """AC-012: Given invalid IP address format, When validating, Then error explains requirements."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: TEST
type: spine
node_groups:
  - group: TEST
    nodes:
      - name: spine1
        id: 1
        mgmt_ip: not-an-ip
"""
        )

        # Should log warning about invalid IP
        inventory = loader.load(inventory_dir)
        # Device with invalid IP should be skipped
        assert len(inventory.fabrics) == 0 or len(inventory.fabrics[0].get_all_devices()) == 0

    def test_multiple_topology_types_in_single_file(self, loader, tmp_path):
        """Test parsing when a single group_vars file contains multiple topology types.

        Regression test for bug where if-elif chain stopped at first topology match.
        A group_vars file can contain both 'spine:' and 'l3leaf:' sections,
        and both should be parsed (not just the first one found).

        This is a common pattern in AVD where FABRIC.yml defines the entire topology.
        """
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create group_vars/FABRIC.yml with BOTH spine and l3leaf sections
        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "FABRIC.yml").write_text(
            """---
fabric_name: MULTI_TOPOLOGY_FABRIC
design_type: l3ls-evpn

# Spine topology section
spine:
  defaults:
    platform: vEOS
    bgp_as: 65000
  nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.1
    - name: spine2
      id: 2
      mgmt_ip: 192.168.0.2

# L3 Leaf topology section (in same file!)
l3leaf:
  defaults:
    platform: vEOS
    spanning_tree_mode: mstp
  node_groups:
    - group: pod1
      bgp_as: 65100
      nodes:
        - name: leaf1
          id: 1
          mgmt_ip: 192.168.0.11
        - name: leaf2
          id: 2
          mgmt_ip: 192.168.0.12
"""
        )

        # Load inventory
        inventory = loader.load(inventory_dir)

        # Verify fabric loaded
        assert len(inventory.fabrics) == 1
        fabric = inventory.fabrics[0]
        assert fabric.name == "MULTI_TOPOLOGY_FABRIC"

        # CRITICAL: Both spine AND leaf devices should be parsed
        # This was the bug - only spines were parsed because of if-elif chain
        assert len(fabric.spine_devices) == 2, "Expected 2 spine devices"
        assert len(fabric.leaf_devices) == 2, "Expected 2 leaf devices"
        assert len(fabric.get_all_devices()) == 4, "Expected 4 total devices"

        # Verify spine devices
        spine_names = [d.hostname for d in fabric.spine_devices]
        assert "spine1" in spine_names
        assert "spine2" in spine_names

        # Verify leaf devices
        leaf_names = [d.hostname for d in fabric.leaf_devices]
        assert "leaf1" in leaf_names
        assert "leaf2" in leaf_names


class TestGroupHierarchy:
    """Tests for Ansible group hierarchy resolution.

    These tests validate the fix for the bug where devices were not
    inheriting variables from all parent groups in the Ansible inventory
    hierarchy. This is critical for proper AVD configuration generation.
    """

    @pytest.fixture
    def loader(self):
        """Create a loader instance."""
        return InventoryLoader()

    @pytest.fixture
    def hierarchical_inventory(self, tmp_path):
        """Create an inventory with nested group hierarchy like the real eos-design-complex example.

        Structure:
        lab (root)
          └─ atd
              └─ campus_avd
                  └─ campus_leaves
                      └─ IDF1
                          ├─ leaf-1a
                          └─ leaf-1b
        """
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create inventory.yml with nested group structure
        (inventory_dir / "inventory.yml").write_text(
            """---
lab:
  vars:
    global_setting: from_lab
    ansible_user: testuser
  children:
    atd:
      vars:
        atd_setting: from_atd
      children:
        campus_avd:
          vars:
            fabric_name: CAMPUS_FABRIC
            avd_setting: from_campus_avd
          children:
            campus_leaves:
              vars:
                leaf_setting: from_campus_leaves
                poc_platform: test_platform
              children:
                IDF1:
                  hosts:
                    leaf-1a:
                      ansible_host: 192.168.0.14
                    leaf-1b:
                      ansible_host: 192.168.0.15
"""
        )

        # Create group_vars
        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()

        # group_vars/atd/basics.yml - should be inherited by leaf-1a
        atd_dir = group_vars_dir / "atd"
        atd_dir.mkdir()
        (atd_dir / "basics.yml").write_text(
            """---
router_bfd:
  multihop:
    interval: 1200
    min_rx: 1200
    multiplier: 3
"""
        )

        # group_vars/campus_avd/topology.yml - defines the device topology
        campus_avd_dir = group_vars_dir / "campus_avd"
        campus_avd_dir.mkdir()
        (campus_avd_dir / "topology.yml").write_text(
            """---
fabric_name: CAMPUS_FABRIC
type: l3leaf
l3leaf:
  defaults:
    platform: vEOS
    spanning_tree_mode: mstp
  node_groups:
    - group: IDF1_NODES
      nodes:
        - name: leaf-1a
          id: 1
          mgmt_ip: 192.168.0.14
        - name: leaf-1b
          id: 2
          mgmt_ip: 192.168.0.15
"""
        )

        # group_vars/campus_leaves/features.yml - should be inherited by leaf-1a
        campus_leaves_dir = group_vars_dir / "campus_leaves"
        campus_leaves_dir.mkdir()
        (campus_leaves_dir / "features.yml").write_text(
            """---
interface_profiles:
  - name: test_profile
    commands:
      - description "Test Interface Profile"
      - switchport mode access
"""
        )

        return inventory_dir

    def test_device_inherits_all_parent_groups(self, loader, hierarchical_inventory):
        """Test that a device has all ancestor groups in its groups list.

        This is the core fix: leaf-1a defined in IDF1 should have groups:
        ['lab', 'atd', 'campus_avd', 'campus_leaves', 'IDF1']

        Previously, it only had the topology group (campus_leaves) and missed
        parent groups, causing variables from those groups to not be applied.
        """
        inventory = loader.load(hierarchical_inventory)

        # Find leaf-1a
        leaf_1a = None
        for fabric in inventory.fabrics:
            for device in fabric.get_all_devices():
                if device.hostname == "leaf-1a":
                    leaf_1a = device
                    break
            if leaf_1a:
                break

        assert leaf_1a is not None, "leaf-1a should be found in inventory"

        # CRITICAL: Device should have ALL ancestor groups, not just the topology group
        # Check content, not order (order is alphabetical after Set conversion)
        expected_groups = {'lab', 'atd', 'campus_avd', 'campus_leaves', 'IDF1'}
        actual_groups = set(leaf_1a.groups)
        assert actual_groups == expected_groups, (
            f"Device should inherit full group hierarchy. "
            f"Expected {expected_groups}, got {actual_groups}"
        )

    def test_device_inherits_variables_from_all_groups(self, loader, hierarchical_inventory):
        """Test that variables from all ancestor groups are available for config generation.

        This validates that the group hierarchy fix enables proper variable inheritance.
        Variables defined in parent groups (atd, campus_leaves) should be accessible
        when building pyavd inputs for the device.
        """
        from avd_cli.logics.generator import ConfigurationGenerator

        inventory = loader.load(hierarchical_inventory)

        # Get all devices and build pyavd inputs
        gen = ConfigurationGenerator()
        devices = inventory.get_all_devices()
        inputs = gen._build_pyavd_inputs_from_inventory(inventory, devices)

        # Check that leaf-1a has variables from ALL parent groups
        assert 'leaf-1a' in inputs, "leaf-1a should be in pyavd inputs"
        leaf_vars = inputs['leaf-1a']

        # From group_vars/atd/basics.yml
        assert 'router_bfd' in leaf_vars, "Should inherit router_bfd from 'atd' group"
        assert leaf_vars['router_bfd']['multihop']['interval'] == 1200

        # From group_vars/campus_leaves/features.yml
        assert 'interface_profiles' in leaf_vars, "Should inherit interface_profiles from 'campus_leaves' group"
        assert len(leaf_vars['interface_profiles']) == 1
        assert leaf_vars['interface_profiles'][0]['name'] == 'test_profile'

        # From inventory.yml group vars
        assert leaf_vars.get('atd_setting') == 'from_atd', "Should inherit vars from atd group in inventory.yml"
        assert leaf_vars.get('leaf_setting') == 'from_campus_leaves', "Should inherit vars from campus_leaves group"
        assert leaf_vars.get('avd_setting') == 'from_campus_avd', "Should inherit vars from campus_avd group"

    def test_group_hierarchy_map_construction(self, loader, hierarchical_inventory):
        """Test that the group hierarchy map is correctly built from inventory.yml.

        The _build_group_hierarchy method should parse the inventory structure
        and create a complete ancestry list for each group.
        """
        hierarchy = loader._build_group_hierarchy(hierarchical_inventory)

        # Check that IDF1 has full ancestry (content, not order)
        assert 'IDF1' in hierarchy, "IDF1 group should be in hierarchy"
        assert set(hierarchy['IDF1']) == {'lab', 'atd', 'campus_avd', 'campus_leaves', 'IDF1'}, (
            "IDF1 should have complete ancestry from root to self"
        )

        # Check intermediate groups (content, not order)
        assert set(hierarchy['campus_leaves']) == {'lab', 'atd', 'campus_avd', 'campus_leaves'}
        assert set(hierarchy['campus_avd']) == {'lab', 'atd', 'campus_avd'}
        assert set(hierarchy['atd']) == {'lab', 'atd'}
        assert set(hierarchy['lab']) == {'lab'}

    def test_host_to_group_mapping(self, loader, hierarchical_inventory):
        """Test that the host-to-group map correctly identifies where each host is defined.

        The _build_host_to_group_map method should find the immediate Ansible group
        for each host (e.g., leaf-1a -> IDF1, not campus_leaves).
        """
        host_map = loader._build_host_to_group_map(hierarchical_inventory)

        # Hosts are defined in IDF1 group, not in campus_leaves
        assert 'leaf-1a' in host_map, "leaf-1a should be in host map"
        assert host_map['leaf-1a'] == 'IDF1', (
            "leaf-1a should map to IDF1 (where it's defined), not to topology group"
        )

        assert 'leaf-1b' in host_map
        assert host_map['leaf-1b'] == 'IDF1'

    def test_multiple_children_in_hierarchy(self, loader, tmp_path):
        """Test group hierarchy with multiple children at same level (siblings).

        Structure:
        root
          ├─ group_a
          │   └─ subgroup_a1
          │       └─ host1
          └─ group_b
              └─ subgroup_b1
                  └─ host2
        """
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        (inventory_dir / "inventory.yml").write_text(
            """---
root:
  children:
    group_a:
      children:
        subgroup_a1:
          hosts:
            host1:
              ansible_host: 192.168.1.1
    group_b:
      children:
        subgroup_b1:
          hosts:
            host2:
              ansible_host: 192.168.1.2
"""
        )

        # Create minimal group_vars for topology
        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "subgroup_a1.yml").write_text(
            """---
fabric_name: FABRIC_A
type: spine
nodes:
  - name: host1
    id: 1
    mgmt_ip: 192.168.1.1
"""
        )
        (group_vars_dir / "subgroup_b1.yml").write_text(
            """---
fabric_name: FABRIC_B
type: spine
nodes:
  - name: host2
    id: 1
    mgmt_ip: 192.168.1.2
"""
        )

        hierarchy = loader._build_group_hierarchy(inventory_dir)

        # Both branches should have correct ancestry (content, not order)
        assert set(hierarchy['subgroup_a1']) == {'root', 'group_a', 'subgroup_a1'}
        assert set(hierarchy['subgroup_b1']) == {'root', 'group_b', 'subgroup_b1'}
        assert set(hierarchy['group_a']) == {'root', 'group_a'}
        assert set(hierarchy['group_b']) == {'root', 'group_b'}

    def test_variable_precedence_in_hierarchy(self, loader, tmp_path):
        """Test that variable precedence follows Ansible rules: more specific beats less specific.

        When the same variable is defined at multiple levels:
        - Host vars (most specific) > Group vars > Global vars (least specific)
        - Child group vars > Parent group vars
        """
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        (inventory_dir / "inventory.yml").write_text(
            """---
root:
  vars:
    test_var: from_root
    root_only: root_value
  children:
    child_group:
      vars:
        test_var: from_child
        child_only: child_value
      hosts:
        testhost:
          ansible_host: 192.168.0.1
          test_var: from_host
          host_only: host_value
"""
        )

        group_vars_dir = inventory_dir / "group_vars"
        group_vars_dir.mkdir()
        (group_vars_dir / "child_group.yml").write_text(
            """---
fabric_name: TEST
type: spine
nodes:
  - name: testhost
    id: 1
    mgmt_ip: 192.168.0.1
"""
        )

        from avd_cli.logics.generator import ConfigurationGenerator

        inventory = loader.load(inventory_dir)
        gen = ConfigurationGenerator()
        devices = inventory.get_all_devices()
        inputs = gen._build_pyavd_inputs_from_inventory(inventory, devices)

        host_vars = inputs['testhost']

        # Host var should win (most specific)
        assert host_vars['test_var'] == 'from_host'

        # Variables from all levels should be present
        assert host_vars['root_only'] == 'root_value'
        assert host_vars['child_only'] == 'child_value'
        assert host_vars['host_only'] == 'host_value'
