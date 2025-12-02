---
goal: "Generate Containerlab topology from AVD inventory"
version: "1.0"
date_created: 2025-12-01
last_updated: 2025-12-01
owner: "avd-cli team"
status: "Completed"
tags: [feature, topology, containerlab]
---

# Introduction

![Status: Completed](https://img.shields.io/badge/status-Completed-green)

Add a `avd-cli generate topology containerlab` command that converts resolved AVD inventory data into a Containerlab topology definition with ceos nodes, management IPs taken from `ansible_host`, explicit graph labels, and startup-config references aligned with `intended/configs/<hostname>.cfg`.

## 1. Requirements & Constraints

- **REQ-001**: The new CLI command must reuse `InventoryLoader` resolution so Containerlab data stays consistent with existing inventory templates.
- **REQ-002**: Each node’s `startup-config` path defaults to `$INVENTORY/intended/configs/<hostname>.cfg` but must be overrideable via `--startup-dir` or `--output-path` logic.
- **REQ-003**: Containerlab output must include `defaults`, `nodes`, and `links` sections that comply with https://containerlab.dev/manual/topo-def-file/ with `kind: ceos` for every node.
- **REQ-004**: The `nodes` section must assign `mgmt-ipv4` from `ansible_host`, deduce `labels.graph-level` from the inventory hierarchy (spine vs leaf), and set a `graph-icon` label for visibility.
- **REQ-005**: `links` must be derived from `ethernet_interfaces` metadata when both `peer` and `peer_interface` are present.
- **CON-001**: No additional dependencies may be introduced; use existing YAML utilities (`yaml.safe_dump`).
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
| TASK-006 | Build `nodes`: iterate `inventory.host_vars`, ensure `ansible_host` exists (log warning otherwise), set `mgmt-ipv4`, `kind`, and `startup-config` path derived from `startup_dir` + `/intended/configs/{hostname}.cfg`, add `labels.graph-level` based on `device_type` (e.g., spines = 0, leaves/member-leaves = 1). | ✅ | 2025-12-01 |
| TASK-007 | Build `links`: for each `ethernet_interfaces` entry containing `peer` and `peer_interface`, create Containerlab link entries referencing hostnames and interface names plus optional channel-group data. Skip entries lacking peers but log the skipped interface. | ✅ | 2025-12-01 |
| TASK-008 | Serialize the Containerlab dictionary via `yaml.safe_dump(..., sort_keys=False)` and write it to `<output_path>/containerlab/topology.yml`, ensuring the output directory exists. | ✅ | 2025-12-01 |

### Implementation Phase 3

- **GOAL-003**: Validate behavior through automated tests and documentation updates.

| Task | Description | Completed | Date |
| --- | --- | --- | --- |
| TASK-009 | Add unit tests in `tests/logics/test_topology.py` to feed synthetic resolved inventory data and assert nodes, defaults, and link generation, including skipped interfaces logging. | ✅ | 2025-12-01 |
| TASK-010 | Add CLI integration test that runs `uv run avd-cli generate topology containerlab -i examples/atd-inventory -o tmp` and verifies `tmp/containerlab/topology.yml` contains expected nodes with `mgmt-ipv4`. | ✅ | 2025-12-01 |
| TASK-011 | Document output schema and option interactions in `README.md` or `docs/generate.md`, explicitly referencing how `startup-config` paths are constructed. | ✅ | 2025-12-01 |

## 3. Alternatives

- **ALT-001**: Reusing generated configs instead of inventory data was rejected because topology metadata (links, defaults) is unavailable in the config output.
- **ALT-002**: Generate JSON and convert post-process was rejected due to spec requiring YAML and readability concerns.

## 4. Dependencies

- **DEP-001**: `InventoryLoader` (`avd_cli/logics/loader.py`) for resolved vars.
- **DEP-002**: YAML serialization via Python standard `yaml.safe_dump` (already used elsewhere).

## 5. Files

- **FILE-001**: `avd_cli/cli/commands/generate.py` – register new command, parse options, route to topology generator.
- **FILE-002**: `avd_cli/logics/topology.py` – host transformation logic and YAML writer.
- **FILE-003**: `tests/logics/test_topology.py` – unit tests for nodes/link generation.
- **FILE-004**: `tests/cli/test_generate_topology.py` (or similar) – CLI integration test verifying output file creation.
- **FILE-005**: `README.md` (or docs) – document CLI usage and startup-config path.

## 6. Testing

- **TEST-001**: Unit test ensuring single-host inventory produces a Containerlab node with `mgmt-ipv4`, proper labels, and no missing `ansible_host` errors.
- **TEST-002**: CLI test running `uv run avd-cli generate topology containerlab -i examples/atd-inventory -o tmp` and verifying topology file content and existence.

## 7. Risks & Assumptions

- **RISK-001**: Some hosts might lack `ansible_host`; the generator must log warnings and skip those hosts gracefully.
- **ASSUMPTION-001**: Every node’s `ethernet_interfaces` entries include both `peer` and `peer_interface` when a Containerlab link is required.
- **ASSUMPTION-002**: `graph-level` can be derived from existing `device_type` or group naming conventions without additional user input.

## 8. Related Specifications / Further Reading
[Containerlab topology definition](https://containerlab.dev/manual/topo-def-file/)
[Existing generate command documentation](README.md)