---
title: Improve Error Messages and User Experience
version: 1.0
date_created: 2025-11-06
status: in-progress
owner: AVD CLI Development Team
tags: [feature, ux, error-handling, user-experience]
---

![Status: in-progress](https://img.shields.io/badge/status-in--progress-yellow)

Improve error messages across the AVD CLI to provide actionable guidance and better user experience, implementing acceptance criteria AC-018, AC-019, and AC-020 from the data schema specification.

## 1. Requirements & Constraints

- **AC-018**: Given validation error, When displaying to user, Then message includes actionable suggestion
- **AC-019**: Given file parsing error, When reporting, Then message shows file path and syntax error location
- **AC-020**: Given schema violation, When reporting, Then message explains expected vs actual structure
- **REQ-008**: CLI shall provide meaningful error messages for invalid operations
- **SEC-004**: Application shall implement proper error handling without exposing internal details
- **QUA-006**: All CLI commands shall have help text and examples

## 2. Implementation Steps

### Implementation Phase 1: Error Message Framework

- GOAL-001: Create structured error message system with actionable suggestions

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Add `suggestion` field to AvdCliError base exception class | | |
| TASK-002 | Add `get_user_message()` method to format errors with context | | |
| TASK-003 | Update ValidationError to include file_path and line_number | | |
| TASK-004 | Add error code system (ERR-001, ERR-002, etc.) for categorization | | |
| TASK-005 | Create error message templates with suggestions | | |

### Implementation Phase 2: Loader Error Improvements

- GOAL-002: Improve error messages in inventory loading

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-006 | Enhance YAML parsing errors to show file path and line number | | |
| TASK-007 | Add suggestions for common YAML syntax errors | | |
| TASK-008 | Improve missing file/directory errors with path information | | |
| TASK-009 | Add schema validation errors with expected vs actual format | | |
| TASK-010 | Test error messages with invalid inventories | | |

### Implementation Phase 3: Validation Error Improvements

- GOAL-003: Enhance device validation error messages

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-011 | Improve "missing required field" errors with field name | | |
| TASK-012 | Enhance IP validation errors with format examples | | |
| TASK-013 | Improve platform validation with list of supported platforms | | |
| TASK-014 | Add hostname validation errors with format requirements | | |
| TASK-015 | Create tests for each validation error type | | |

### Implementation Phase 4: CLI Error Display

- GOAL-004: Improve error display in CLI commands

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-016 | Format errors with Rich for better readability | | |
| TASK-017 | Add error panels with suggestions | | |
| TASK-018 | Include error codes in CLI output | | |
| TASK-019 | Add --debug flag to show stack traces | | |
| TASK-020 | Test error display in all CLI commands | | |

## 3. Alternatives

- **ALT-001**: Use exception chaining only - rejected because less explicit than custom error codes
- **ALT-002**: Implement separate error handler class - deferred for future if complexity increases

## 4. Dependencies

- **DEP-001**: Rich library - already installed for terminal formatting
- **DEP-002**: Existing exception classes in avd_cli/exceptions.py
- **DEP-003**: YAML library error handling capabilities

## 5. Files

- **FILE-001**: `avd_cli/exceptions.py` - Add suggestion field and error codes
- **FILE-002**: `avd_cli/logics/loader.py` - Improve error messages
- **FILE-003**: `avd_cli/models/inventory.py` - Enhance validation errors
- **FILE-004**: `avd_cli/cli/main.py` - Format errors with Rich
- **FILE-005**: `tests/unit/test_exceptions.py` - Test error messages (NEW)

## 6. Testing

- **TEST-001**: Test each error type displays with actionable suggestion
- **TEST-002**: Test YAML parsing errors show file path and line number
- **TEST-003**: Test validation errors explain expected vs actual format
- **TEST-004**: Test error display in CLI with Rich formatting
- **TEST-005**: Test --debug flag shows full stack traces

## 7. Risks & Assumptions

- **RISK-001**: Error messages might expose internal structure - mitigated by careful message templating
- **ASSUMPTION-001**: Users prefer actionable suggestions over technical details
- **ASSUMPTION-002**: File paths and line numbers are always available during parsing

## 8. Related Specifications

- [Data AVD Inventory Schema](../spec/data-avd-inventory-schema.md) - AC-018, AC-019, AC-020
- [Tool AVD CLI Architecture](../spec/tool-avd-cli-architecture.md) - REQ-008, SEC-004
