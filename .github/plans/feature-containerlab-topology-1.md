---
goal: "Generate Containerlab topology from AVD inventory"
version: "1.3"
date_created: 2025-12-01
last_updated: 2025-12-02
owner: "avd-cli team"
status: "In progress"
tags: [feature, topology, containerlab, enhancement, bug]
---

# Introduction

![Status: In progress](https://img.shields.io/badge/status-In%20progress-yellow)

Add a `avd-cli generate topology containerlab` command that converts resolved AVD inventory data into a Containerlab topology definition with ceos nodes, management IPs taken from `ansible_host`, explicit graph labels, and startup-config references aligned with `configs/<hostname>.cfg`.

**Version 1.1 Enhancement**: Add support for uplink topology generation using AVD l3leaf/l2leaf structure fields (`uplink_interfaces`, `uplink_switches`, `uplink_switch_interfaces`) to construct fabric links in addition to existing `ethernet_interfaces` peer-based links.

## 1. Requirements & Constraints

- **REQ-001**: The new CLI command must reuse `InventoryLoader` resolution so Containerlab data stays consistent with existing inventory templates.
- **REQ-002**: Each node's `startup-config` path is computed as relative path from topology file (e.g., `../configs/<hostname>.cfg`) and defaults to `$OUTPUT_PATH/configs/<hostname>.cfg`, overrideable via `--startup-dir`.
- **REQ-003**: Containerlab output must include `name`, `topology.nodes`, and `topology.links` sections that comply with <https://containerlab.dev/manual/topo-def-file/> with `kind: ceos` for every node. The `defaults` section is NOT part of Containerlab spec and was removed in v1.1.
- **REQ-004**: The `nodes` section must assign `mgmt-ipv4` from `ansible_host`, deduce `labels.graph-level` from the **dynamically-computed network topology hierarchy** (not just device type names), and set a `graph-icon` label for visibility. **CRITICAL**: `graph-level` uses values 1-9 where 9 is the highest level in the network hierarchy.
- **REQ-011**: The `graph-level` label must be computed dynamically by analyzing actual network connectivity patterns (uplink relationships, peer connections) rather than relying solely on device type string matching. Devices with no uplinks (core/spine) receive higher values; devices with uplinks (leafs/access) receive lower values proportional to their distance from core.
- **REQ-012**: Hierarchy determination algorithm must analyze: (1) uplink topology (`uplink_switches` defines parent-child relationships), (2) peer connections (`ethernet_interfaces` with `peer` fields), (3) device type hints as fallback only. Compute graph depth/level for each device to assign appropriate `graph-level` values.
- **REQ-005**: `links` must be derived from two sources: (1) `ethernet_interfaces` metadata when both `peer` and `peer_interface` are present, (2) AVD structure fields `uplink_interfaces`, `uplink_switches`, and `uplink_switch_interfaces` from l3leaf/l2leaf node definitions.
- **REQ-006**: When building uplink-based links, iterate through parallel arrays `uplink_interfaces[i]`, `uplink_switches[i]`, and `uplink_switch_interfaces[i]` to construct link endpoints as `<local_hostname>:<uplink_interface>` to `<uplink_switch>:<uplink_switch_interface>`.
- **REQ-007**: Links from uplink definitions must be deduplicated against existing `ethernet_interfaces`-based links using the same sorted tuple key mechanism.
- **REQ-008**: Node `kind` must be configurable via CLI option `--kind` with default value `ceos` to support alternative node types (e.g., `vr-arista_veos`).
- **REQ-009**: Node `image` must be configurable with flexible options: `--image` for complete image string, or component options `--image-registry`, `--image-name`, `--image-version` with defaults `arista`, `ceos`, `latest` respectively.
- **REQ-010**: Image construction must follow priority: if `--image` provided, use as-is; otherwise construct `{registry}/{name}:{version}` from component options.
- **CON-001**: No additional dependencies may be introduced; use existing YAML utilities (`yaml.safe_dump`).
- **CON-002**: Startup config paths must be relative to topology YAML file location for portability.
- **GUD-001**: Comment only when explaining why a decision exists; code must be self-documenting to honor repository style.
- **PAT-001**: Tasks must be deterministic and reference exact files/functions so future automation can execute them without interpretation.
- **SEC-001**: CLI command behavior remains unchanged for non-root execution scenarios.

## 2. Implementation Steps

### Implementation Phase 1

- **GOAL-001**: Extend the CLI command tree to expose `generate topology containerlab` with options for inventory, output, startup directory, and node kind.

| Task | Description | Completed | Date |
| --- | --- | --- | --- |
| TASK-001 | Update `avd_cli/cli/commands/generate.py` to add a `containerlab` subparser under `generate topology`, reusing `InventoryConfig` options and accepting `--startup-dir` (default `$INVENTORY/intended/configs`), `--kind` (default `ceos`), and an optional `--topology-name`. | ✅ | 2025-12-01 |
| TASK-002 | Wire the new command to call a dedicated `ContainerlabTopologyGenerator` with resolved `InventoryData` and parsed CLI options, ensuring `--output-path` is reused for the topology file destination. | ✅ | 2025-12-01 |
| TASK-003 | Update CLI help text and `README.md` to mention the new command, its options, and the expected `startup-config` resolution. | ✅ | 2025-12-01 |

### Implementation Phase 2

- **GOAL-002**: Implement the Containerlab transformation logic that consumes resolved inventory data and writes compliant YAML.

| Task | Description | Completed | Date |
| --- | --- | --- | --- |
| TASK-004 | Create `avd_cli/logics/topology.py` introducing `ContainerlabTopologyGenerator` with a `generate()` method that accepts `InventoryData`, options (`startup_dir`, `node_kind`, `topology_name`), and returns a dict matching Containerlab structure. | ✅ | 2025-12-01 |
| TASK-005 | Implement defaults extraction: inspect `l2leaf`/`l3leaf` structures in resolved group vars for `defaults` and merge with CLI-specified fallback pools and interface arrays. | ✅ | 2025-12-01 |
| TASK-006 | Build `nodes`: iterate `inventory.host_vars`, ensure `ansible_host` exists (log warning otherwise), set `mgmt-ipv4`, `kind`, and `startup-config` path derived from `startup_dir` + `/intended/configs/{hostname}.cfg`, add `labels.graph-level` based on `device_type` (e.g., spines = higher value, leaves/member-leaves = lower value). **BUG IDENTIFIED**: Current implementation incorrectly assigns spines=0 and leafs=1, which is inverted. | ⚠️ | 2025-12-01 |
| TASK-007 | Build `links`: for each `ethernet_interfaces` entry containing `peer` and `peer_interface`, create Containerlab link entries referencing hostnames and interface names plus optional channel-group data. Skip entries lacking peers but log the skipped interface. | ✅ | 2025-12-01 |
| TASK-008 | Serialize the Containerlab dictionary via `yaml.safe_dump(..., sort_keys=False)` and write it to `<output_path>/containerlab/topology.yml`, ensuring the output directory exists. | ✅ | 2025-12-01 |
| TASK-012 | Update `_build_links()` in `avd_cli/logics/topology.py` to extract uplink topology from `group_vars`: create `_extract_uplink_data()` method to retrieve `uplink_interfaces`, `uplink_switches`, and `uplink_switch_interfaces` from AVD l3leaf/l2leaf structure, then iterate using `zip()` to create link endpoints. | ✅ | 2025-12-02 |
| TASK-013 | Add validation in `_build_links()` to ensure uplink arrays have matching lengths before iteration. Log warning if array lengths mismatch and skip that device's uplink links. | ✅ | 2025-12-02 |
| TASK-014 | Extend link deduplication logic to handle both `ethernet_interfaces` and uplink-based links using the existing `seen` set with sorted tuple keys. | ✅ | 2025-12-02 |

### Implementation Phase 3

- **GOAL-003**: Validate behavior through automated tests and documentation updates.

| Task | Description | Completed | Date |
| --- | --- | --- | --- |
| TASK-009 | Add unit tests in `tests/logics/test_topology.py` to feed synthetic resolved inventory data and assert nodes, defaults, and link generation, including skipped interfaces logging. | ✅ | 2025-12-01 |
| TASK-010 | Add CLI integration test that runs `uv run avd-cli generate topology containerlab -i examples/atd-inventory -o tmp` and verifies `tmp/containerlab/topology.yml` contains expected nodes with `mgmt-ipv4`. | ✅ | 2025-12-01 |
| TASK-011 | Document output schema and option interactions in `README.md` or `docs/generate.md`, explicitly referencing how `startup-config` paths are constructed. | ✅ | 2025-12-01 |
| TASK-015 | Update unit tests in `tests/logics/test_topology.py` to include test cases with synthetic `uplink_interfaces`, `uplink_switches`, and `uplink_switch_interfaces` data, asserting correct link generation from uplink topology. Added `test_containerlab_topology_with_uplinks()` and `test_containerlab_topology_uplink_deduplication()`. | ✅ | 2025-12-02 |
| TASK-016 | Add integration test validating uplink-based links are generated correctly with real AVD inventory structure (l3leaf/l2leaf with uplink fields). Manual testing with examples/eos-design-basics confirms 8 links generated correctly. | ✅ | 2025-12-02 |

### Implementation Phase 4

- **GOAL-004**: Correct existing implementation issues discovered during v1.1 development.

| Task | Description | Completed | Date |
| --- | --- | --- | --- |
| TASK-017 | Remove `_extract_defaults()` method and `defaults` section from topology output as it is not part of Containerlab spec (completed in v1.1 bugfix). | ✅ | 2025-12-02 |
| TASK-018 | Fix `--startup-dir` default from `intended/configs` to `configs` and update help text to clarify path is relative to output path, not inventory path (completed in v1.1 bugfix). | ✅ | 2025-12-02 |
| TASK-019 | Implement relative path computation in `_compute_relative_path()` from topology file to startup config files for portability (completed in v1.1 bugfix). | ✅ | 2025-12-02 |

### Implementation Phase 5

- **GOAL-005**: Add support for configurable node kind and Docker image for Containerlab nodes.

| Task | Description | Completed | Date |
| --- | --- | --- | --- |
| TASK-020 | Add CLI options to `generate topology containerlab`: `--kind` (default `ceos`), `--image` (complete image string), `--image-registry` (default `arista`), `--image-name` (default `ceos`), `--image-version` (default `latest`). | ✅ | 2025-12-02 |
| TASK-021 | Implement image string construction logic: if `--image` provided, use as-is; otherwise build `{registry}/{name}:{version}` from component options. | ✅ | 2025-12-02 |
| TASK-022 | Update `_build_nodes()` in `topology.py` to accept `kind` and `image` parameters and include them in node definitions. | ✅ | 2025-12-02 |
| TASK-023 | Add unit tests verifying image construction logic with various option combinations (default, version-only, full image, custom registry). Added `test_containerlab_topology_custom_image()` testing multiple scenarios. | ✅ | 2025-12-02 |
| TASK-024 | Update documentation in `docs/user-guide/commands/generate.md` with examples for custom images and registries. Added comprehensive section on Docker image configuration with priority explanation and common scenarios. | ✅ | 2025-12-02 |

### Implementation Phase 6

- **GOAL-006**: Implement dynamic topology-based hierarchy computation for graph-level assignment instead of static device type mapping.

| Task | Description | Completed | Date |
| --- | --- | --- | --- |
| TASK-025 | Implement `_compute_topology_hierarchy()` method in `avd_cli/logics/topology.py` that analyzes uplink relationships from `group_vars` (l3leaf/l2leaf `uplink_switches` arrays) and `ethernet_interfaces` peer connections to build a directed graph of parent-child device relationships. | | |
| TASK-026 | Implement graph traversal algorithm to compute "distance from core" for each device: devices with no parents (no uplinks, no upstream peers) are core/root nodes; calculate maximum depth from each device to any root node. Store depth in `device_depths: Dict[str, int]`. | | |
| TASK-027 | Replace `_graph_level()` method with dynamic computation: `graph_level = max_depth - device_depth + 1` where `max_depth` is the deepest device in topology. This ensures core devices (depth=0) receive highest values (e.g., 9), leafs (depth=1) receive lower values (e.g., 8), access devices (depth=2) receive even lower (e.g., 7). | | |
| TASK-028 | Add fallback logic in `_graph_level()`: if device not found in computed hierarchy (isolated device), use device_type string matching as fallback with conservative default (graph-level=5 for unknown types). | | |
| TASK-029 | Update `_build_nodes()` to call topology hierarchy computation once before iterating devices, then look up each device's computed graph-level from the hierarchy map. | | |
| TASK-030 | Add unit tests in `tests/unit/logics/test_topology.py` verifying dynamic hierarchy computation: test topology with spine→leaf uplinks produces spine>leaf values; test MPLS topology with P→PE uplinks produces P>PE values; test isolated devices use fallback. | | |
| TASK-031 | Add integration test with `examples/eos-design-basics/` validating generated topology has correct hierarchy (spines have higher graph-level than leafs based on uplink analysis, not string matching). | | |
| TASK-032 | Update documentation to explain dynamic topology-based hierarchy computation algorithm, including uplink analysis, graph traversal, and fallback behavior. Include examples for L3LS-EVPN, MPLS, and custom topologies. | | |

## 3. Alternatives

- **ALT-001**: Reusing generated configs instead of inventory data was rejected because topology metadata (links, defaults) is unavailable in the config output.
- **ALT-002**: Generate JSON and convert post-process was rejected due to spec requiring YAML and readability concerns.
- **ALT-003**: Using only `ethernet_interfaces` for links was insufficient as it misses spine-to-leaf uplinks defined via AVD structure fields. Hybrid approach using both sources was chosen.
- **ALT-004**: Computing absolute paths for `startup-config` was rejected in favor of relative paths for better portability across environments.
- **ALT-005**: Hardcoding `arista/ceos:latest` was rejected; users need flexibility for custom registries (GitHub, Harbor), different versions for testing, and alternative node kinds (vrnetlab).
- **ALT-006**: Static device type string matching for graph-level (spine=9, leaf=1) was rejected because topologies vary (MPLS P-PE, custom designs). Dynamic topology analysis via uplink relationships provides universal solution that adapts to any hierarchy.

## 4. Dependencies

- **DEP-001**: `InventoryLoader` (`avd_cli/logics/loader.py`) for resolved vars.
- **DEP-002**: YAML serialization via Python standard `yaml.safe_dump` (already used elsewhere).

## 5. Files

- **FILE-001**: `avd_cli/cli/main.py` – register new command group `generate topology containerlab`, parse options, route to topology generator (actual implementation location, not `commands/generate.py`).
- **FILE-002**: `avd_cli/logics/topology.py` – host transformation logic, link generation from both `ethernet_interfaces` and uplink structures, YAML writer with relative paths.
- **FILE-003**: `tests/logics/test_topology.py` – unit tests for nodes/link generation including uplink-based links.
- **FILE-004**: `README.md` – document CLI usage, startup-config path resolution, and link generation behavior.

## 6. Testing

- **TEST-001**: Unit test ensuring single-host inventory produces a Containerlab node with `mgmt-ipv4`, proper labels, and no missing `ansible_host` errors.
- **TEST-002**: CLI test running `uv run avd-cli generate topology containerlab -i examples/eos-design-basics -o tmp` and verifying topology file content and existence.
- **TEST-003**: Unit test with synthetic inventory containing `uplink_interfaces`, `uplink_switches`, and `uplink_switch_interfaces` arrays to verify uplink-based link generation.
- **TEST-004**: Unit test verifying link deduplication works correctly when same link is defined in both `ethernet_interfaces` and uplink structures.
- **TEST-005**: Unit test with mismatched uplink array lengths to verify warning logging and graceful handling.
- **TEST-006**: Verify relative path computation produces correct `../configs/hostname.cfg` format in generated topology.
- **TEST-007**: Unit test verifying `_compute_topology_hierarchy()` correctly analyzes uplink relationships: given synthetic inventory with leaf→spine uplinks, asserts spines have depth=0 and leafs have depth=1.
- **TEST-008**: Unit test for MPLS topology: given PE devices with uplinks to P routers, asserts P routers (depth=0) receive higher graph-level than PE routers (depth=1).
- **TEST-009**: Unit test for multi-tier topology: given access→distribution→core uplink chain, asserts core (depth=0) > distribution (depth=1) > access (depth=2) in computed hierarchy.
- **TEST-010**: Unit test for isolated device fallback: device not in uplink graph uses device_type string matching as fallback.
- **TEST-011**: Integration test with `examples/eos-design-basics/`: generate topology, parse YAML, assert s1-spine1 has `graph-level` > s1-leaf1's `graph-level` (dynamic computation based on uplinks).
- **TEST-012**: Integration test with `examples/eos-design-mpls/`: verify P routers have higher graph-level than PE routers based on uplink topology analysis.

## 7. Risks & Assumptions

- **RISK-001**: Some hosts might lack `ansible_host`; the generator must log warnings and skip those hosts gracefully.
- **RISK-002**: Uplink arrays (`uplink_interfaces`, `uplink_switches`, `uplink_switch_interfaces`) may have mismatched lengths; validation must detect and log warnings for such cases.
- **RISK-003**: Uplink switches referenced in `uplink_switches` may not be present in the filtered device list; links to missing nodes must be skipped silently.
- **RISK-004**: Incorrect graph-level assignment causes topology visualization to display network hierarchy upside-down in Containerlab, potentially confusing users about actual network architecture.
- **ASSUMPTION-001**: Every node's `ethernet_interfaces` entries include both `peer` and `peer_interface` when a Containerlab link is required.
- **ASSUMPTION-002**: `graph-level` can be derived from existing `device_type` or group naming conventions without additional user input.
- **ASSUMPTION-003**: AVD l3leaf/l2leaf structures always define uplink topology using parallel arrays with matching indices for interfaces, switches, and switch interfaces.
- **ASSUMPTION-004**: Startup configs are expected to exist at `<output_path>/configs/` by default, matching typical AVD generation workflow.
- **ASSUMPTION-005**: Containerlab `graph-level` visualization follows standard network hierarchy where higher-tier devices (core/spine) receive numerically higher values than lower-tier devices (distribution/leaf/access).
- **ASSUMPTION-006**: Network topology hierarchy can be reliably inferred from uplink relationships (`uplink_switches`) and peer connections (`ethernet_interfaces.peer`), with devices having no uplinks being topmost (core/spine layer).
- **ASSUMPTION-007**: Topologies may vary (L3LS-EVPN spine-leaf, MPLS P-PE, custom multi-tier) and device type names are not reliable indicators of hierarchy; actual connectivity patterns must be analyzed dynamically.

## 8. Related Specifications / Further Reading

- [Containerlab topology definition](https://containerlab.dev/manual/topo-def-file/)
- [Existing generate command documentation](README.md)
