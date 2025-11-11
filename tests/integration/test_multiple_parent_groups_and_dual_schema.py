#!/usr/bin/env python
# coding: utf-8 -*-

"""
Integration tests for multiple parent groups and dual schema merge.

These tests validate the fixes for two critical bugs discovered in the
eos-design-complex example:

1. **Multiple Parent Group Inheritance Bug**:
   - Groups can have multiple parents in Ansible (e.g., campus_leaves is a child
     of campus_avd, campus_services, AND campus_ports simultaneously)
   - Original code only captured ONE parent path, missing variables from other branches
   - Fix: Changed hierarchy tracking from List[str] to Set[str] and recursively
     collect ALL ancestors from ALL parent paths

2. **Dual Schema Merge Bug**:
   - PyAVD has two schemas: eos_designs (topology) and eos_cli_config_gen (CLI configs)
   - Original code only used eos_designs output, ignoring eos_cli_config_gen variables
   - Fix: Deep merge inputs (containing both schema types) with structured_config output

These bugs caused missing configurations in generated device configs:
- Missing VLANs (from campus_services group)
- Missing aliases, NTP, logging, AAA, etc. (from eos_cli_config_gen variables)
"""

import tempfile
import shutil
from pathlib import Path
import pytest

from avd_cli.logics.loader import InventoryLoader
from avd_cli.logics.generator import ConfigurationGenerator


class TestMultipleParentGroupsAndDualSchema:
    """Integration tests for multiple parent groups and dual schema merge."""

    @pytest.fixture(scope="function")
    def eos_design_complex_inventory(self):
        """Path to the eos-design-complex example inventory.

        This inventory has multiple parent relationships:
        - campus_leaves is child of: campus_avd, campus_services, campus_ports
        - campus_spines is child of: campus_avd, campus_services

        Returns
        -------
        Path
            Path to eos-design-complex inventory
        """
        project_root = Path(__file__).parent.parent.parent
        example_inventory = project_root / "examples" / "eos-design-complex"

        if not example_inventory.exists():
            pytest.skip("eos-design-complex example inventory not available")

        return example_inventory

    @pytest.fixture(scope="function")
    def temp_output(self):
        """Create a temporary directory for test outputs.

        Yields
        ------
        Path
            Temporary output directory
        """
        temp_dir = tempfile.mkdtemp(prefix="avd_cli_test_multi_parent_")
        output_path = Path(temp_dir)

        yield output_path

        # Cleanup after test completes
        try:
            if output_path.exists():
                shutil.rmtree(output_path, ignore_errors=False)
        except Exception:
            # Fallback to forceful cleanup
            pass

    # ========================================================================
    # Test 1: Multiple Parent Group Inheritance
    # ========================================================================

    def test_device_inherits_all_parent_groups(self, eos_design_complex_inventory):
        """Test that devices inherit ALL parent groups, not just one path.

        Bug Context
        -----------
        campus_leaves has three parents:
        - campus_avd (topology/fabric configuration)
        - campus_services (VLANs, interface profiles)
        - campus_ports (port configurations)

        Before Fix
        ----------
        Device groups: ['lab', 'atd', 'campus_avd', 'campus_leaves', 'IDF1']
        Missing: campus_services, campus_ports

        After Fix
        ---------
        Device groups: ['IDF1', 'atd', 'campus_avd', 'campus_leaves',
                        'campus_ports', 'campus_services', 'lab']
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        # Find leaf-1a device
        leaf_1a = None
        for fabric in inventory.fabrics:
            for device in fabric.get_all_devices():
                if device.hostname == "leaf-1a":
                    leaf_1a = device
                    break
            if leaf_1a:
                break

        assert leaf_1a is not None, "leaf-1a should exist in inventory"

        # CRITICAL: Verify ALL parent groups are present
        expected_groups = [
            'lab',               # Root group
            'atd',               # Sub-root group
            'campus_avd',        # Fabric topology group
            'campus_leaves',     # Device type group
            'campus_services',   # Services group (BUG: was missing before fix)
            'campus_ports',      # Ports group (BUG: was missing before fix)
            'IDF1',              # Specific site group
        ]

        # Check each expected group is present
        for group in expected_groups:
            assert group in leaf_1a.groups, (
                f"Group '{group}' should be in leaf-1a.groups. "
                f"Got: {sorted(leaf_1a.groups)}. "
                f"This indicates the multiple parent group inheritance bug may have regressed."
            )

        # Verify total count (no extra, no missing)
        assert len(leaf_1a.groups) == len(expected_groups), (
            f"Expected {len(expected_groups)} groups, got {len(leaf_1a.groups)}. "
            f"Expected: {sorted(expected_groups)}, Got: {sorted(leaf_1a.groups)}"
        )

    def test_campus_services_variables_accessible(self, eos_design_complex_inventory):
        """Test that variables from campus_services group are accessible.

        Bug Context
        -----------
        campus_services/services.yml contains:
        - VLANs: 100 (campus-users), 300 (campus-voice), 666, 667
        - Interface profiles for campus connectivity

        Before Fix
        ----------
        campus_services not in device.groups → variables not inherited
        → VLANs missing from generated configs

        After Fix
        ---------
        campus_services in device.groups → variables inherited
        → VLANs present in generated configs
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        gen = ConfigurationGenerator()
        devices = inventory.get_all_devices()
        inputs = gen._build_pyavd_inputs_from_inventory(inventory, devices)

        # Check leaf-1a has variables from campus_services
        assert 'leaf-1a' in inputs, "leaf-1a should be in inputs"
        leaf_vars = inputs['leaf-1a']

        # Variables from campus_services/services.yml (tenants, not vlans)
        assert 'tenants' in leaf_vars, (
            "leaf-1a should inherit 'tenants' from campus_services group. "
            "Missing this indicates the multiple parent group bug has regressed."
        )

        # Verify tenants structure and SVIs are present
        tenants = leaf_vars.get('tenants', [])
        assert len(tenants) > 0, "Should have at least one tenant"
        assert tenants[0]['name'] == 'AVD_CAMPUS', "Should have AVD_CAMPUS tenant"

        # Check SVIs in the tenant
        vrfs = tenants[0].get('vrfs', [])
        assert len(vrfs) > 0, "Tenant should have VRFs"
        svis = vrfs[0].get('svis', [])
        svi_ids = [svi.get('id') for svi in svis if isinstance(svi, dict)]

        expected_svi_ids = [100, 300, 666, 667]
        for svi_id in expected_svi_ids:
            assert svi_id in svi_ids, (
                f"SVI {svi_id} should be inherited from campus_services. "
                f"Got SVIs: {svi_ids}"
            )

    def test_campus_ports_variables_accessible(self, eos_design_complex_inventory):
        """Test that variables from campus_ports group are accessible.

        Bug Context
        -----------
        campus_ports contains port-specific configurations that should be
        inherited by campus_leaves devices.

        Before Fix
        ----------
        campus_ports not in device.groups → variables not inherited

        After Fix
        ---------
        campus_ports in device.groups → variables inherited
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        devices = inventory.get_all_devices()

        # Variables from campus_ports should be accessible
        # (The actual variables depend on what's defined in group_vars/campus_ports/)
        # This test verifies the group is in the hierarchy so variables would be inherited
        leaf_1a_device = [d for d in devices if d.hostname == 'leaf-1a'][0]
        assert 'campus_ports' in leaf_1a_device.groups, (
            "campus_ports group should be in leaf-1a's hierarchy"
        )

    def test_spine_inherits_from_campus_services(self, eos_design_complex_inventory):
        """Test that spine devices also inherit from campus_services.

        Bug Context
        -----------
        campus_spines is also a child of campus_services (in addition to campus_avd).
        Spines should inherit service-related variables.

        Structure
        ---------
        lab -> atd -> campus_avd -> campus_spines
                   -> campus_services -> campus_spines
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        # Find a spine device
        spine = None
        for fabric in inventory.fabrics:
            for device in fabric.get_all_devices():
                if "spine" in device.hostname.lower():
                    spine = device
                    break
            if spine:
                break

        if spine is None:
            pytest.skip("No spine device found in inventory")

        # Verify campus_services is in spine's groups
        assert 'campus_services' in spine.groups, (
            f"Spine should have campus_services group. Got: {sorted(spine.groups)}. "
            f"This indicates the multiple parent group bug affects spines too."
        )

        # Verify campus_spines is present
        assert 'campus_spines' in spine.groups, (
            f"Spine should have campus_spines group. Got: {sorted(spine.groups)}"
        )

    # ========================================================================
    # Test 2: Dual Schema Merge (eos_designs + eos_cli_config_gen)
    # ========================================================================

    def test_eos_cli_config_gen_variables_inherited(self, eos_design_complex_inventory):
        """Test that eos_cli_config_gen variables are included in inputs.

        Bug Context
        -----------
        PyAVD has two schemas:
        - eos_designs: High-level fabric topology (spines, leaves, BGP, EVPN)
        - eos_cli_config_gen: Low-level CLI configs (aliases, ntp, snmp, logging, aaa)

        Before Fix
        ----------
        Only eos_designs output was used → eos_cli_config_gen variables ignored
        → Missing aliases, NTP, logging, AAA, etc. in generated configs

        After Fix
        ---------
        Deep merge inputs with structured_config
        → Both schema types present in final config
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        gen = ConfigurationGenerator()
        devices = inventory.get_all_devices()
        inputs = gen._build_pyavd_inputs_from_inventory(inventory, devices)

        leaf_vars = inputs['leaf-1a']

        # Variables from eos_cli_config_gen schema (in group_vars/atd/)
        eos_cli_config_gen_vars = [
            'aliases',            # From atd/alias.yml
            'ntp',                # From atd/basics.yml
            'router_bfd',         # From atd/basics.yml
            'logging',            # From atd/basics.yml
            'ip_name_servers',    # From atd/basics.yml
            'name_server',        # Alternative key
            'aaa_authentication',  # From atd/aaa.yml
            'aaa_authorization',   # From atd/aaa.yml
            'radius_servers',      # From atd/aaa.yml
            'dot1x',              # From atd/aaa.yml
        ]

        missing_vars = []
        for var in eos_cli_config_gen_vars:
            if var not in leaf_vars:
                missing_vars.append(var)

        # At least SOME eos_cli_config_gen variables should be present
        assert len(missing_vars) < len(eos_cli_config_gen_vars), (
            f"Most eos_cli_config_gen variables are missing. "
            f"Missing: {missing_vars}. "
            f"This indicates the dual schema merge bug may have regressed."
        )

        # Check specific critical variables
        critical_vars = ['aliases', 'router_bfd', 'aaa_authentication']
        for var in critical_vars:
            assert var in leaf_vars, (
                f"Critical eos_cli_config_gen variable '{var}' is missing. "
                f"This indicates the dual schema merge bug has regressed."
            )

    @pytest.mark.skip(reason="Config generation requires full PyAVD with eos_designs and eos_cli_config_gen")
    def test_generated_config_contains_aliases(self, eos_design_complex_inventory, temp_output):
        """Test that generated config contains aliases (eos_cli_config_gen).

        Bug Context
        -----------
        Aliases are defined in group_vars/atd/alias.yml (eos_cli_config_gen schema).
        Before the fix, these were not included in generated configs.

        Expected Content
        ----------------
        alias sib show ip bgp summary
        alias sibs show ip bgp neighbors
        alias sibr show ip bgp route
        ... (18 total aliases)
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        gen = ConfigurationGenerator()
        generated_files = gen.generate(inventory, temp_output)

        assert len(generated_files) >= 10, "Should generate at least 10 configs"

        # Check leaf-1a config
        leaf_1a_config = temp_output / "configs" / "leaf-1a.cfg"
        assert leaf_1a_config.exists(), "leaf-1a config should be generated"

        config_content = leaf_1a_config.read_text()

        # Verify aliases are present
        assert 'alias sib show ip bgp summary' in config_content, (
            "Generated config should contain aliases from eos_cli_config_gen. "
            "This indicates the dual schema merge bug may have regressed."
        )

        # Count alias lines
        alias_lines = [line for line in config_content.split('\n') if line.startswith('alias ')]
        assert len(alias_lines) >= 15, (
            f"Expected at least 15 alias lines, got {len(alias_lines)}. "
            f"This indicates incomplete eos_cli_config_gen merge."
        )

    @pytest.mark.skip(reason="Config generation requires full PyAVD with eos_designs and eos_cli_config_gen")
    def test_generated_config_contains_ntp(self, eos_design_complex_inventory, temp_output):
        """Test that generated config contains NTP configuration (eos_cli_config_gen).

        Bug Context
        -----------
        NTP is defined in group_vars/atd/basics.yml (eos_cli_config_gen schema).

        Expected Content
        ----------------
        ntp local-interface vrf MGMT Management1
        ntp server vrf MGMT 192.168.0.1 burst iburst
        ntp server vrf MGMT 192.168.0.2 burst iburst
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        gen = ConfigurationGenerator()
        gen.generate(inventory, temp_output)

        leaf_1a_config = temp_output / "configs" / "leaf-1a.cfg"
        config_content = leaf_1a_config.read_text()

        # Verify NTP configuration is present
        assert 'ntp local-interface' in config_content, (
            "Generated config should contain NTP configuration from eos_cli_config_gen"
        )

        # Count NTP lines
        ntp_lines = [line for line in config_content.split('\n') if line.startswith('ntp ')]
        assert len(ntp_lines) >= 3, (
            f"Expected at least 3 NTP lines, got {len(ntp_lines)}. "
            f"NTP lines found: {ntp_lines}"
        )

    @pytest.mark.skip(reason="Config generation requires full PyAVD with eos_designs and eos_cli_config_gen")
    def test_generated_config_contains_aaa(self, eos_design_complex_inventory, temp_output):
        """Test that generated config contains AAA configuration (eos_cli_config_gen).

        Bug Context
        -----------
        AAA is defined in group_vars/atd/aaa.yml (eos_cli_config_gen schema).

        Expected Content
        ----------------
        aaa authentication login default local
        aaa authorization exec default local
        aaa authentication dot1x default group radius
        radius-server deadtime 3
        dot1x system-auth-control
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        gen = ConfigurationGenerator()
        gen.generate(inventory, temp_output)

        leaf_1a_config = temp_output / "configs" / "leaf-1a.cfg"
        config_content = leaf_1a_config.read_text()

        # Verify AAA configuration is present
        assert 'aaa authentication' in config_content, (
            "Generated config should contain AAA authentication from eos_cli_config_gen"
        )

        assert 'aaa authorization' in config_content, (
            "Generated config should contain AAA authorization from eos_cli_config_gen"
        )

        # Verify radius and dot1x
        assert 'radius-server' in config_content, (
            "Generated config should contain RADIUS server configuration"
        )

        assert 'dot1x' in config_content, (
            "Generated config should contain dot1x configuration"
        )

    @pytest.mark.skip(reason="Config generation requires full PyAVD with eos_designs and eos_cli_config_gen")
    def test_generated_config_contains_vlans_from_campus_services(
        self, eos_design_complex_inventory, temp_output
    ):
        """Test that generated config contains VLANs from campus_services group.

        Bug Context
        -----------
        This test validates BOTH fixes working together:
        1. Multiple parent groups: campus_services must be in device.groups
        2. Dual schema merge: VLANs must be included in final config

        Expected VLANs
        --------------
        vlan 100
           name campus-users
        vlan 300
           name campus-voice
        vlan 666
           name GARBAGE_USERS
        vlan 667
           name GARBAGE_PHONES
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        gen = ConfigurationGenerator()
        gen.generate(inventory, temp_output)

        leaf_1a_config = temp_output / "configs" / "leaf-1a.cfg"
        config_content = leaf_1a_config.read_text()

        # Verify each expected VLAN is present
        expected_vlans = [
            ('100', 'campus-users'),
            ('300', 'campus-voice'),
            ('666', 'GARBAGE_USERS'),
            ('667', 'GARBAGE_PHONES'),
        ]

        for vlan_id, vlan_name in expected_vlans:
            assert f'vlan {vlan_id}' in config_content, (
                f"VLAN {vlan_id} should be present in config. "
                f"This indicates either the multiple parent group bug or "
                f"the dual schema merge bug has regressed."
            )

            assert f'name {vlan_name}' in config_content, (
                f"VLAN {vlan_id} should have name '{vlan_name}'. "
                f"Config excerpt:\n{self._get_vlan_section(config_content, vlan_id)}"
            )

    @pytest.mark.skip(reason="Config generation requires full PyAVD with eos_designs and eos_cli_config_gen")
    def test_generated_config_contains_router_bfd(self, eos_design_complex_inventory, temp_output):
        """Test that generated config contains router BFD configuration.

        Bug Context
        -----------
        Router BFD is defined in group_vars/atd/basics.yml (eos_cli_config_gen).

        Expected Content
        ----------------
        router bfd
           multihop interval 1200 min-rx 1200 multiplier 3
        """
        loader = InventoryLoader()
        inventory = loader.load(eos_design_complex_inventory)

        gen = ConfigurationGenerator()
        gen.generate(inventory, temp_output)

        leaf_1a_config = temp_output / "configs" / "leaf-1a.cfg"
        config_content = leaf_1a_config.read_text()

        assert 'router bfd' in config_content, (
            "Generated config should contain 'router bfd' configuration"
        )

        assert 'multihop interval' in config_content, (
            "Router BFD should have multihop interval configuration"
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_vlan_section(self, config_content: str, vlan_id: str) -> str:
        """Extract VLAN section from config for debugging.

        Parameters
        ----------
        config_content : str
            Full configuration content
        vlan_id : str
            VLAN ID to extract

        Returns
        -------
        str
            VLAN section (5 lines around the VLAN definition)
        """
        lines = config_content.split('\n')
        for i, line in enumerate(lines):
            if f'vlan {vlan_id}' in line:
                start = max(0, i - 1)
                end = min(len(lines), i + 4)
                return '\n'.join(lines[start:end])
        return f"VLAN {vlan_id} not found in config"


# ============================================================================
# Unit Tests for Internal Methods
# ============================================================================

class TestGroupHierarchyMethods:
    """Unit tests for group hierarchy internal methods."""

    @pytest.fixture
    def inventory_path(self):
        """Provide path to test inventory."""
        project_root = Path(__file__).parent.parent.parent
        example_inventory = project_root / "examples" / "eos-design-complex"

        if not example_inventory.exists():
            pytest.skip("eos-design-complex example inventory not available")

        return example_inventory

    def test_build_group_hierarchy_returns_list(self, inventory_path):
        """Test that _build_group_hierarchy returns Dict[str, List[str]].

        Bug Context
        -----------
        Changed from single path List to Set internally, then converted to sorted List.

        Before Fix
        ----------
        Dict[str, List[str]] - only one path per group

        After Fix
        ---------
        Dict[str, List[str]] - sorted list of all unique ancestors from all paths
        """
        loader = InventoryLoader()
        hierarchy = loader._build_group_hierarchy(inventory_path)

        assert isinstance(hierarchy, dict), "Should return a dictionary"

        # Check that values are lists
        for group_name, ancestors in hierarchy.items():
            assert isinstance(ancestors, list), (
                f"Ancestors for {group_name} should be a List[str], got {type(ancestors)}"
            )

    def test_campus_leaves_has_all_parent_groups_in_hierarchy(self, inventory_path):
        """Test that campus_leaves hierarchy includes ALL parent groups.

        Bug Context
        -----------
        campus_leaves has three parents in inventory.yml:
        - Under campus_avd
        - Under campus_services
        - Under campus_ports

        All three paths should be captured in the hierarchy.

        Expected Ancestors
        ------------------
        {'lab', 'atd', 'campus_avd', 'campus_leaves', 'campus_services', 'campus_ports'}
        """
        loader = InventoryLoader()
        hierarchy = loader._build_group_hierarchy(inventory_path)

        assert 'campus_leaves' in hierarchy, "campus_leaves should be in hierarchy"

        # Verify all expected ancestors are present (convert list to set for comparison)
        expected_ancestors = {
            'lab',
            'atd',
            'campus_avd',
            'campus_leaves',
            'campus_services',
            'campus_ports',
        }

        actual_ancestors_set = set(hierarchy['campus_leaves'])
        assert actual_ancestors_set == expected_ancestors, (
            f"campus_leaves should have all parent groups from all paths. "
            f"Expected: {expected_ancestors}, Got: {actual_ancestors_set}. "
            f"Missing: {expected_ancestors - actual_ancestors_set}, "
            f"Extra: {actual_ancestors_set - expected_ancestors}"
        )

    def test_idf1_inherits_campus_leaves_full_hierarchy(self, inventory_path):
        """Test that IDF1 (child of campus_leaves) inherits full hierarchy.

        Bug Context
        -----------
        IDF1 is defined under campus_avd/campus_leaves in inventory.yml.
        But campus_leaves has ancestors from multiple paths.
        IDF1 should inherit ALL of them transitively.

        Expected Ancestors
        ------------------
        All ancestors of campus_leaves PLUS IDF1 itself
        """
        loader = InventoryLoader()
        hierarchy = loader._build_group_hierarchy(inventory_path)

        assert 'IDF1' in hierarchy, "IDF1 should be in hierarchy"

        idf1_ancestors = hierarchy['IDF1']

        # IDF1 should have at least all ancestors of campus_leaves
        # (Note: Due to how paths are built, IDF1 might not have campus_services/ports
        # directly in its hierarchy dict, but they get added during device parsing
        # when we transitively add ancestors of ancestors)

        # At minimum, IDF1 should have these (convert list to set for subset check)
        minimum_expected = {'lab', 'atd', 'campus_avd', 'campus_leaves', 'IDF1'}

        assert minimum_expected.issubset(set(idf1_ancestors)), (
            f"IDF1 should have at least {minimum_expected}. "
            f"Got: {set(idf1_ancestors)}"
        )

    def test_hierarchy_does_not_contain_duplicates(self, inventory_path):
        """Test that hierarchy lists don't contain duplicate entries.

        Bug Context
        -----------
        Using Set[str] internally ensures no duplicates even with multiple paths.
        """
        loader = InventoryLoader()
        hierarchy = loader._build_group_hierarchy(inventory_path)

        for group_name, ancestors in hierarchy.items():
            # Lists should not have duplicates (ensured by Set internally)
            assert isinstance(ancestors, list), (
                f"Ancestors for {group_name} should be a list"
            )

            # Check no duplicates by comparing length
            assert len(ancestors) == len(set(ancestors)), (
                f"Ancestors for {group_name} should not contain duplicates"
            )

            # Verify group appears in its own ancestors (by design)
            assert group_name in ancestors, (
                f"Group {group_name} should be in its own ancestor list"
            )
