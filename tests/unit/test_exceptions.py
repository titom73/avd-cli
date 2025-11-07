#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for custom exceptions."""

import pytest

from avd_cli.exceptions import (
    AvdCliError,
    ConfigurationGenerationError,
    DocumentationGenerationError,
    FileSystemError,
    InvalidInventoryError,
    TemplateError,
    TestGenerationError,
    ValidationError,
    WorkflowError,
)


class TestAvdCliExceptions:
    """Test custom exception classes."""

    def test_base_exception_inheritance(self):
        """Test that all custom exceptions inherit from AvdCliError."""
        # Test each exception individually to avoid type issues
        assert issubclass(InvalidInventoryError, AvdCliError)
        assert issubclass(ConfigurationGenerationError, AvdCliError)
        assert issubclass(DocumentationGenerationError, AvdCliError)
        assert issubclass(TestGenerationError, AvdCliError)
        assert issubclass(ValidationError, AvdCliError)
        assert issubclass(FileSystemError, AvdCliError)
        assert issubclass(WorkflowError, AvdCliError)
        assert issubclass(TemplateError, AvdCliError)

        # Test inheritance from Exception
        assert issubclass(AvdCliError, Exception)

    def test_avd_cli_error_base(self):
        """Test base AvdCliError exception."""
        # Test with message
        error = AvdCliError("Test error message")
        assert str(error) == "Test error message"

        # Test without message
        error = AvdCliError()
        assert str(error) == ""

        # Test raising
        with pytest.raises(AvdCliError) as exc_info:
            raise AvdCliError("Base error")

        assert str(exc_info.value) == "Base error"

    def test_invalid_inventory_error(self):
        """Test InvalidInventoryError exception."""
        message = "group_vars directory not found"

        with pytest.raises(InvalidInventoryError) as exc_info:
            raise InvalidInventoryError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_configuration_generation_error(self):
        """Test ConfigurationGenerationError exception."""
        message = "Failed to generate config for device: spine1"

        with pytest.raises(ConfigurationGenerationError) as exc_info:
            raise ConfigurationGenerationError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_documentation_generation_error(self):
        """Test DocumentationGenerationError exception."""
        message = "Failed to generate documentation for fabric"

        with pytest.raises(DocumentationGenerationError) as exc_info:
            raise DocumentationGenerationError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_test_generation_error(self):
        """Test TestGenerationError exception."""
        message = "Failed to generate ANTA catalog"

        with pytest.raises(TestGenerationError) as exc_info:
            raise TestGenerationError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_validation_error(self):
        """Test ValidationError exception."""
        message = "Invalid IP address format: 192.168.0.256"

        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_file_system_error(self):
        """Test FileSystemError exception."""
        message = "Cannot write to directory: /protected/output"

        with pytest.raises(FileSystemError) as exc_info:
            raise FileSystemError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_workflow_error(self):
        """Test WorkflowError exception."""
        message = "Workflow state transition failed"

        with pytest.raises(WorkflowError) as exc_info:
            raise WorkflowError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_template_error(self):
        """Test TemplateError exception."""
        message = "Undefined variable 'platform' in template"

        with pytest.raises(TemplateError) as exc_info:
            raise TemplateError(message)

        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, AvdCliError)

    def test_exception_chaining(self):
        """Test exception chaining with custom exceptions."""
        original_error = ValueError("Original error")

        with pytest.raises(ConfigurationGenerationError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise ConfigurationGenerationError("Configuration failed") from e

        assert str(exc_info.value) == "Configuration failed"
        assert exc_info.value.__cause__ is original_error

    def test_exception_hierarchy_catch(self):
        """Test that specific exceptions can be caught by base class."""
        # Test that we can catch specific exceptions with base class
        with pytest.raises(AvdCliError):
            raise InvalidInventoryError("Inventory error")

        with pytest.raises(AvdCliError):
            raise ConfigurationGenerationError("Config error")

        with pytest.raises(AvdCliError):
            raise ValidationError("Validation error")

    def test_exception_with_context(self):
        """Test exceptions with additional context."""
        error = ConfigurationGenerationError("Failed for device spine01")

        with pytest.raises(ConfigurationGenerationError) as exc_info:
            raise error

        assert "spine01" in str(exc_info.value)

    def test_exception_docstrings(self):
        """Test that all exceptions have proper docstrings."""
        # Test each exception individually
        assert AvdCliError.__doc__ is not None
        assert InvalidInventoryError.__doc__ is not None
        assert ConfigurationGenerationError.__doc__ is not None
        assert DocumentationGenerationError.__doc__ is not None
        assert TestGenerationError.__doc__ is not None
        assert ValidationError.__doc__ is not None
        assert FileSystemError.__doc__ is not None
        assert WorkflowError.__doc__ is not None
        assert TemplateError.__doc__ is not None

    def test_multiple_exception_types(self):
        """Test handling multiple exception types in try/except."""

        def raise_different_errors(error_type: str):
            if error_type == "inventory":
                raise InvalidInventoryError("Bad inventory")
            if error_type == "config":
                raise ConfigurationGenerationError("Config failed")
            if error_type == "validation":
                raise ValidationError("Invalid data")
            raise AvdCliError("Generic error")

        # Test catching specific types
        with pytest.raises(InvalidInventoryError):
            raise_different_errors("inventory")

        with pytest.raises(ConfigurationGenerationError):
            raise_different_errors("config")

        with pytest.raises(ValidationError):
            raise_different_errors("validation")

        # Test catching with base class
        with pytest.raises(AvdCliError):
            raise_different_errors("other")

    def test_exception_args_property(self):
        """Test that exception args are properly set."""
        message = "Test error with multiple args"

        error = AvdCliError(message)

        assert error.args == (message,)
        assert str(error) == message  # String representation
