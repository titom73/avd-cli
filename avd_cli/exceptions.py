#!/usr/bin/env python
# coding: utf-8 -*-

"""Custom exceptions for AVD CLI.

This module defines all custom exceptions used throughout the AVD CLI application.
"""


class AvdCliError(Exception):
    """Base exception for all AVD CLI errors.

    All custom exceptions in the AVD CLI inherit from this base class.
    """

    pass


class InvalidInventoryError(AvdCliError):
    """Raised when AVD inventory structure is invalid.

    This exception is raised when the inventory directory structure
    does not meet AVD requirements or contains invalid data.

    Examples
    --------
    >>> raise InvalidInventoryError("group_vars directory not found")
    """

    pass


class ConfigurationGenerationError(AvdCliError):
    """Raised when configuration generation fails.

    This exception is raised when the configuration generation process
    encounters an error that prevents successful completion.

    Examples
    --------
    >>> raise ConfigurationGenerationError("Failed to generate config for device: spine1")
    """

    pass


class DocumentationGenerationError(AvdCliError):
    """Raised when documentation generation fails.

    This exception is raised when the documentation generation process
    encounters an error that prevents successful completion.
    """

    pass


class TestGenerationError(AvdCliError):
    """Raised when ANTA test generation fails.

    This exception is raised when the ANTA test generation process
    encounters an error that prevents successful completion.
    """

    pass


class ValidationError(AvdCliError):
    """Raised when data validation fails.

    This exception is raised when input data fails validation checks.

    Examples
    --------
    >>> raise ValidationError("Invalid IP address format: 192.168.0.256")
    """

    pass


class FileSystemError(AvdCliError):
    """Raised when file system operations fail.

    This exception is raised when file I/O operations encounter errors
    such as permission denied, file not found, etc.

    Examples
    --------
    >>> raise FileSystemError("Cannot write to directory: /protected/output")
    """

    pass


class WorkflowError(AvdCliError):
    """Raised when workflow execution fails.

    This exception is raised when the workflow state machine encounters
    an error during execution.
    """

    pass


class TemplateError(AvdCliError):
    """Raised when Jinja2 template resolution fails.

    This exception is raised when template variables cannot be resolved
    or when template syntax is invalid.

    Examples
    --------
    >>> raise TemplateError("Undefined variable 'platform' in template")
    """
