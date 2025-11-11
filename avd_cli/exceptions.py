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

    pass


class DeploymentError(AvdCliError):
    """Raised when configuration deployment fails.

    This exception is raised when the deployment process encounters
    an error that prevents successful completion.

    Examples
    --------
    >>> raise DeploymentError("Failed to deploy config to device: spine1")
    """

    pass


class ConnectionError(AvdCliError):
    """Raised when device connection fails.

    This exception is raised when unable to establish connection
    to target device via eAPI.

    Examples
    --------
    >>> raise ConnectionError("Cannot connect to 192.168.0.10:443 - connection timeout")
    """

    pass


class AuthenticationError(AvdCliError):
    """Raised when device authentication fails.

    This exception is raised when authentication to device
    fails due to invalid credentials.

    Examples
    --------
    >>> raise AuthenticationError("Authentication failed for device: spine1")
    """

    pass


class ConfigurationError(AvdCliError):
    """Raised when configuration syntax is invalid.

    This exception is raised when device rejects configuration
    due to syntax errors or invalid commands.

    Examples
    --------
    >>> raise ConfigurationError("Invalid command at line 45: interface Ethernet1/1")
    """

    pass


class CredentialError(AvdCliError):
    """Raised when credentials are missing or invalid.

    This exception is raised when required credentials
    (ansible_user, ansible_password) are not found in inventory.

    Examples
    --------
    >>> raise CredentialError("ansible_user not found for device: leaf01")
    """
