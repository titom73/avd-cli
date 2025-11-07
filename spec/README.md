# AVD CLI Specifications

This directory contains comprehensive specifications for the AVD CLI project. Each specification defines requirements, interfaces, and implementation guidelines for different aspects of the system.

## 📋 Available Specifications

### 🔧 [Tool: AVD CLI Architecture](./tool-avd-cli-architecture.md)

**Purpose**: Defines the overall architecture, design patterns, and technical requirements for the AVD CLI tool.

**Key Topics**:

- CLI interface design and command structure
- Layered architecture (CLI → Logic → Models)
- Technology stack (Click, Rich, pytest, UV)
- Code quality standards and metrics
- Error handling and logging strategies

**Audience**: All developers, AI assistants, code reviewers

---

### 🔄 [Process: AVD Workflow Processing](./process-avd-workflow.md)

**Purpose**: Defines the workflow processes for AVD inventory processing, validation, and artifact generation.

**Key Topics**:

- Workflow state machine and execution stages
- Full workflow vs. config-only modes
- Validation gates and error handling
- Progress tracking and reporting
- Incremental generation strategy

**Audience**: Workflow implementers, integration developers

---

### 📊 [Data: AVD Inventory Schema](./data-avd-inventory-schema.md)

**Purpose**: Defines data structures, validation rules, and contracts for AVD inventory processing.

**Key Topics**:

- Inventory directory structure requirements
- YAML schema for group_vars and host_vars
- Data models (DeviceDefinition, FabricDefinition, InventoryData)
- Validation rules and error messages
- Type safety with dataclasses

**Audience**: Data model implementers, validation logic developers

---

### 🧪 [Infrastructure: Testing Strategy](./infrastructure-testing-strategy.md)

**Purpose**: Defines comprehensive testing strategy, coverage requirements, and quality assurance practices.

**Key Topics**:

- Unit, integration, and E2E testing approaches
- pytest configuration and best practices
- Test fixtures and mocking strategies
- >80% coverage requirements
- CI/CD integration

**Audience**: Test writers, QA engineers, CI/CD maintainers

---

## 🎯 How to Use These Specifications

### For Developers

1. **Starting a New Feature**:
   - Read relevant specifications first
   - Understand requirements and constraints
   - Follow established patterns and interfaces
   - Write tests according to testing strategy

2. **Code Reviews**:
   - Verify changes align with specifications
   - Check acceptance criteria are met
   - Ensure test coverage meets requirements
   - Validate error handling follows patterns

3. **Troubleshooting**:
   - Reference specifications for expected behavior
   - Check validation criteria for compliance
   - Review examples and edge cases
   - Consult rationale for design decisions

### For AI Coding Assistants (GitHub Copilot)

These specifications provide comprehensive context for code generation:

- **Architecture Spec**: Understand overall system design
- **Process Spec**: Generate workflow and state management code
- **Data Spec**: Create data models and validation logic
- **Testing Spec**: Generate comprehensive test suites

Always:

- Follow patterns defined in specifications
- Meet acceptance criteria for features
- Include tests for new functionality
- Maintain consistency with existing code

### For New Contributors

1. Start with [Tool Architecture](./tool-avd-cli-architecture.md) for overview
2. Read [Data Schema](./data-avd-inventory-schema.md) to understand data structures
3. Review [Process Workflow](./process-avd-workflow.md) for business logic
4. Study [Testing Strategy](./infrastructure-testing-strategy.md) before writing tests

## 📐 Specification Structure

Each specification follows a consistent template:

1. **Introduction**: Overview and purpose
2. **Purpose & Scope**: What's covered and who it's for
3. **Definitions**: Key terms and concepts
4. **Requirements, Constraints & Guidelines**: The rules
5. **Interfaces & Data Contracts**: APIs and schemas
6. **Acceptance Criteria**: How to verify compliance
7. **Test Automation Strategy**: Testing approach
8. **Rationale & Context**: Why decisions were made
9. **Dependencies**: External requirements
10. **Examples & Edge Cases**: Practical demonstrations
11. **Validation Criteria**: Compliance checks
12. **Related Specifications**: Cross-references

## 🔄 Specification Lifecycle

### Creating New Specifications

Use the [create-specification.prompt.md](../.github/prompts/create-specification.prompt.md) template to create new specs.

**Naming Convention**: `[type]-[purpose].md`

**Types**:

- `tool-*`: Tool and application specifications
- `process-*`: Workflow and process specifications
- `data-*`: Data schema and structure specifications
- `infrastructure-*`: Infrastructure and system specifications
- `design-*`: Design pattern and UI specifications
- `schema-*`: Technical schema definitions
- `architecture-*`: System architecture specifications

### Updating Specifications

1. Update version number in front matter
2. Update `last_updated` date
3. Document changes in git commit message
4. Notify team of significant changes
5. Update related specifications if needed

### Deprecating Specifications

1. Add `deprecated: true` to front matter
2. Add deprecation notice at top of document
3. Link to replacement specification
4. Keep file for historical reference

## 🔗 Related Documentation

- [GitHub Copilot Instructions](../.github/copilot/copilot-instructions.md): AI-specific coding guidelines
- [Python Instructions](../.github/instructions/python.instructions.md): Python coding standards
- [Testing Instructions](../.github/instructions/testing.instructions.md): Testing guidelines
- [DevOps Principles](../.github/instructions/devops-core-principles.instructions.md): DevOps practices

## 📝 Contributing to Specifications

### Specification Quality Guidelines

- **Clear and Unambiguous**: Use precise language
- **Structured**: Follow template consistently
- **Testable**: Include verifiable acceptance criteria
- **Complete**: Cover all aspects of the topic
- **Maintainable**: Easy to update as system evolves

### When to Create a New Specification

Create a new specification when:

- Starting a major new feature or component
- Defining a new subsystem or module
- Establishing standards for a domain
- Documenting complex business logic
- Defining integration points

### Review Process

1. Create specification as draft
2. Review with team for completeness
3. Validate acceptance criteria are testable
4. Get approval from technical lead
5. Merge and announce to team

## 📞 Questions?

If you have questions about:

- **Specification content**: Consult the specification owner
- **How to use specs**: Review this README and examples
- **Creating new specs**: Use the template in `.github/prompts/`
- **General guidance**: Check related documentation links above

---

**Last Updated**: 2025-11-06
**Maintained By**: AVD CLI Development Team
