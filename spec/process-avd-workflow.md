---
title: AVD Workflow Processing Specification
version: 1.0
date_created: 2025-11-06
last_updated: 2025-11-06
owner: AVD CLI Development Team
tags: [process, workflow, avd, automation]
---

# Introduction

This specification defines the workflow processes for AVD inventory processing, including the two supported approaches (full eos_design + eos_cli_config_gen and config-only eos_cli_config_gen), validation steps, and error handling procedures.

## 1. Purpose & Scope

### Purpose

Define the step-by-step processes for:

- AVD inventory validation and loading
- Configuration generation workflows
- Documentation generation
- ANTA test generation
- Error handling and recovery

### Scope

- Detailed workflow execution steps
- Data transformation between stages
- Validation checkpoints
- Error handling procedures
- Output artifact generation

### Audience

- Development team implementing workflow logic
- AI coding assistants
- Operations team running the CLI
- Integration developers

### Assumptions

- AVD inventory follows standard Ansible inventory structure
- py-avd library is properly configured
- File system has appropriate read/write permissions

## 2. Definitions

- **Workflow**: Sequential process for transforming AVD inventory into outputs
- **Stage**: Individual step in workflow execution
- **Artifact**: Generated output file (config, documentation, test)
- **Validation Gate**: Checkpoint that must pass before proceeding
- **Rollback**: Process of reverting partial changes on error
- **Idempotency**: Ability to run workflow multiple times with same result

## 3. Requirements, Constraints & Guidelines

### Workflow Requirements

- **REQ-001**: Workflow shall validate inventory before processing
- **REQ-002**: Workflow shall support both full and config-only modes
- **REQ-003**: Workflow shall generate outputs incrementally per device
- **REQ-004**: Workflow shall track progress and provide status updates
- **REQ-005**: Workflow shall handle errors gracefully with partial rollback
- **REQ-006**: Workflow shall be idempotent - repeated runs produce same results
- **REQ-007**: Workflow shall log all operations for troubleshooting
- **REQ-008**: Workflow shall validate generated outputs before completion

### Process Requirements

- **PRC-001**: Each stage shall complete or fail atomically
- **PRC-002**: Failed stages shall not affect completed stages
- **PRC-003**: Progress shall be displayed for operations >2 seconds
- **PRC-004**: Errors shall include context and suggested remediation
- **PRC-005**: Cleanup shall occur on terminal errors

### Performance Requirements

- **PER-001**: Validation stage shall complete in <2 seconds
- **PER-002**: Configuration generation shall process 10+ devices/second
- **PER-003**: Documentation generation shall not exceed 2x config generation time
- **PER-004**: Test generation shall complete in <1 second per device

### Constraints

- **CON-001**: Must work within py-avd library API constraints
- **CON-002**: Must handle inventories up to 1000 devices
- **CON-003**: Must operate with limited memory (streaming where possible)
- **CON-004**: Must support parallel processing for independent devices

### Guidelines

- **GUD-001**: Fail fast on validation errors
- **GUD-002**: Provide detailed progress information
- **GUD-003**: Log all file operations
- **GUD-004**: Clean up temporary files on exit
- **GUD-005**: Support graceful interruption (CTRL+C)

## 4. Interfaces & Data Contracts

### Workflow State Machine

```python
from enum import Enum, auto
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

class WorkflowStage(Enum):
    """Workflow execution stages."""
    INIT = auto()
    VALIDATING = auto()
    LOADING = auto()
    GENERATING_CONFIGS = auto()
    GENERATING_DOCS = auto()
    GENERATING_TESTS = auto()
    COMPLETING = auto()
    COMPLETED = auto()
    FAILED = auto()

class WorkflowMode(Enum):
    """Workflow execution modes."""
    FULL = "full"  # eos_design + eos_cli_config_gen + docs
    CONFIG_ONLY = "config-only"  # eos_cli_config_gen only

@dataclass
class WorkflowContext:
    """Context passed through workflow stages."""
    inventory_path: Path
    output_path: Path
    mode: WorkflowMode
    generate_tests: bool
    limit_to_groups: List[str]
    verbose: bool

@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    success: bool
    stage: WorkflowStage
    configs_generated: int
    docs_generated: int
    tests_generated: int
    errors: List[str]
    warnings: List[str]
    artifacts: Dict[str, List[Path]]
```

### Stage Input/Output Contracts

```python
from typing import Protocol

class WorkflowStageHandler(Protocol):
    """Protocol for workflow stage handlers."""

    def can_execute(self, context: WorkflowContext) -> bool:
        """Check if stage can execute with given context."""
        ...

    def execute(self, context: WorkflowContext) -> WorkflowResult:
        """Execute stage and return result."""
        ...

    def rollback(self, context: WorkflowContext) -> None:
        """Rollback stage changes on failure."""
        ...
```

## 5. Acceptance Criteria

### Workflow Execution

- **AC-001**: Given valid inventory, When full workflow executes, Then configs, docs, and tests are generated
- **AC-002**: Given config-only mode, When workflow executes, Then only configs are generated
- **AC-003**: Given limited groups, When workflow executes, Then only specified groups are processed
- **AC-004**: Given validation failure, When workflow starts, Then execution stops before generation
- **AC-005**: Given partial failure, When error occurs mid-process, Then completed artifacts are preserved

### Progress Tracking

- **AC-006**: Given long operation, When workflow executes, Then progress bar displays current stage and percentage
- **AC-007**: Given verbose mode, When workflow executes, Then detailed logs are displayed for each step
- **AC-008**: Given completion, When workflow finishes, Then summary table shows all generated artifacts

### Error Handling

- **AC-009**: Given missing file, When loading inventory, Then clear error message indicates missing file path
- **AC-010**: Given invalid YAML, When parsing inventory, Then error shows file, line number, and syntax issue
- **AC-011**: Given permission error, When writing output, Then error suggests permission fix
- **AC-012**: Given interrupted execution, When user presses CTRL+C, Then partial artifacts are cleaned up

## 6. Test Automation Strategy

### Workflow Testing

- **Unit Tests**: Test individual stage handlers in isolation
- **Integration Tests**: Test complete workflows with sample inventories
- **State Tests**: Test state transitions and error recovery
- **Rollback Tests**: Verify cleanup on failures

### Test Data

- **Valid Inventory**: Complete AVD inventory with all required fields
- **Minimal Inventory**: Smallest valid inventory for quick tests
- **Invalid Inventories**: Various failure scenarios (missing files, bad YAML, etc.)
- **Large Inventory**: 100+ devices for performance testing

### Test Scenarios

```python
def test_full_workflow_success(sample_inventory, tmp_output):
    """Test successful full workflow execution."""
    context = WorkflowContext(
        inventory_path=sample_inventory,
        output_path=tmp_output,
        mode=WorkflowMode.FULL,
        generate_tests=True,
        limit_to_groups=[],
        verbose=False
    )

    result = execute_workflow(context)

    assert result.success
    assert result.stage == WorkflowStage.COMPLETED
    assert result.configs_generated > 0
    assert result.docs_generated > 0
    assert result.tests_generated > 0
    assert len(result.errors) == 0

def test_validation_failure_stops_workflow(invalid_inventory, tmp_output):
    """Test workflow stops on validation failure."""
    context = WorkflowContext(
        inventory_path=invalid_inventory,
        output_path=tmp_output,
        mode=WorkflowMode.FULL,
        generate_tests=False,
        limit_to_groups=[],
        verbose=False
    )

    result = execute_workflow(context)

    assert not result.success
    assert result.stage == WorkflowStage.FAILED
    assert len(result.errors) > 0
    assert result.configs_generated == 0  # Nothing generated
```

## 7. Rationale & Context

### Why State Machine Pattern?

Using a state machine for workflow management provides:

- **Clear States**: Explicit stages make debugging easier
- **Error Recovery**: Each state can define rollback behavior
- **Progress Tracking**: Current state enables accurate progress reporting
- **Testability**: Each state transition can be tested independently
- **Extensibility**: New stages can be added without affecting existing ones

### Why Incremental Generation?

Processing devices incrementally rather than all-at-once enables:

- **Memory Efficiency**: Only one device in memory at a time
- **Fault Tolerance**: Failure on one device doesn't affect others
- **Progress Reporting**: Real-time updates on per-device progress
- **Parallelization**: Independent devices can be processed concurrently
- **Partial Success**: Some devices can succeed even if others fail

### Why Validation Gates?

Validation checkpoints before expensive operations prevent:

- **Wasted Processing**: Don't generate if inventory is invalid
- **Partial Failures**: Catch errors before writing files
- **Resource Waste**: Don't consume CPU/memory for doomed operations
- **Poor UX**: Fail fast with clear messages rather than cryptic errors later

## 8. Dependencies & External Integrations

### External Systems

- **EXT-001**: py-avd Library - Core AVD processing functionality
- **EXT-002**: File System - Inventory input and artifact output storage
- **EXT-003**: ANTA Framework - Test file format specifications

### Data Dependencies

- **DAT-001**: AVD Inventory YAML - Standard Ansible inventory structure
- **DAT-002**: AVD Schema - Implicit data model from py-avd
- **DAT-003**: Device Templates - Jinja2 templates for config generation

### Technology Platform Dependencies

- **PLT-001**: Python 3.9+ - Async/await support for concurrent processing
- **PLT-002**: py-avd Library - AVD processing APIs
- **PLT-003**: PyYAML - YAML parsing and validation
- **PLT-004**: Jinja2 - Template rendering engine

## 9. Examples & Edge Cases

### Full Workflow Execution

```python
# Full workflow with all features enabled
from avd_cli.workflow import WorkflowExecutor
from pathlib import Path

executor = WorkflowExecutor()

result = executor.execute(
    inventory_path=Path("./inventory"),
    output_path=Path("./output"),
    mode="full",
    generate_tests=True,
    limit_to_groups=["spine", "leaf"],
    verbose=True
)

if result.success:
    print(f"✓ Generated {result.configs_generated} configs")
    print(f"✓ Generated {result.docs_generated} docs")
    print(f"✓ Generated {result.tests_generated} tests")
else:
    print(f"✗ Workflow failed at stage: {result.stage}")
    for error in result.errors:
        print(f"  - {error}")
```

### Config-Only Workflow

```python
# Faster workflow for config-only generation
result = executor.execute(
    inventory_path=Path("./inventory"),
    output_path=Path("./output"),
    mode="config-only",
    generate_tests=False,
    limit_to_groups=[],
    verbose=False
)

# Only configs are generated, docs and tests skipped
assert result.docs_generated == 0
assert result.tests_generated == 0
```

### Error Handling Examples

```python
# Handle validation errors
try:
    result = executor.execute(...)
    if not result.success:
        if result.stage == WorkflowStage.VALIDATING:
            print("Inventory validation failed:")
            for error in result.errors:
                print(f"  - {error}")
        elif result.stage == WorkflowStage.GENERATING_CONFIGS:
            print("Config generation failed:")
            print(f"  Successfully generated: {result.configs_generated}")
            print(f"  Errors: {len(result.errors)}")
except KeyboardInterrupt:
    print("Workflow interrupted by user")
    executor.cleanup()
except Exception as e:
    print(f"Unexpected error: {e}")
    executor.cleanup()
```

### Edge Cases

#### Empty Group Filter

```python
# Given: limit_to_groups is empty list
# Expected: All groups are processed
result = executor.execute(
    inventory_path=Path("./inventory"),
    output_path=Path("./output"),
    mode="full",
    generate_tests=False,
    limit_to_groups=[],  # Empty = all groups
    verbose=False
)
# All devices in inventory are processed
```

#### Non-Existent Group

```python
# Given: limit_to_groups contains non-existent group
# Expected: Warning issued, only valid groups processed
result = executor.execute(
    inventory_path=Path("./inventory"),
    output_path=Path("./output"),
    mode="full",
    generate_tests=False,
    limit_to_groups=["spine", "invalid_group"],
    verbose=False
)
assert "invalid_group" in result.warnings
assert result.configs_generated > 0  # spine group still processed
```

#### Partial Device Failure

```python
# Given: One device fails validation, others succeed
# Expected: Workflow continues, failure logged
result = executor.execute(...)
assert result.success  # Overall success
assert len(result.errors) > 0  # But some errors logged
assert result.configs_generated < total_devices  # Not all succeeded
```

#### Output Directory Exists

```python
# Given: Output directory already exists with files
# Expected: Files are overwritten or merged based on config
result = executor.execute(
    inventory_path=Path("./inventory"),
    output_path=Path("./existing_output"),
    mode="full",
    generate_tests=False,
    limit_to_groups=[],
    verbose=False
)
# Existing files are preserved unless overwritten by new generation
```

## 10. Validation Criteria

### Workflow Validation

- **VAL-001**: Workflow completes all stages in correct order
- **VAL-002**: State transitions follow defined state machine
- **VAL-003**: Progress updates occur at expected intervals
- **VAL-004**: Rollback executes on failures

### Output Validation

- **VAL-005**: Generated configs are valid EOS syntax
- **VAL-006**: Generated docs are valid Markdown
- **VAL-007**: Generated tests are valid ANTA YAML
- **VAL-008**: All output files have correct permissions

### Error Handling Validation

- **VAL-009**: All error messages include context and suggestions
- **VAL-010**: Partial artifacts cleaned up on terminal failure
- **VAL-011**: Validation errors prevent further processing
- **VAL-012**: Non-terminal errors allow continuation

### Performance Validation

- **VAL-013**: Validation completes within performance targets
- **VAL-014**: Generation throughput meets requirements
- **VAL-015**: Memory usage stays within bounds
- **VAL-016**: Concurrent processing improves performance

## 11. Related Specifications / Further Reading

### Internal Specifications

- [Tool: AVD CLI Architecture](./tool-avd-cli-architecture.md)
- [Data: AVD Inventory Schema](./data-avd-inventory-schema.md)
- [Design: Error Handling Patterns](./design-error-handling.md)

### External Documentation

- [Arista AVD Roles Documentation](https://avd.arista.com/5.7/roles/)
- [py-avd API Reference](https://avd.arista.com/5.7/docs/pyavd/pyavd.html)
- [ANTA Test Catalog](https://anta.arista.com/stable/api/tests/)
- [State Machine Pattern](https://refactoring.guru/design-patterns/state)
