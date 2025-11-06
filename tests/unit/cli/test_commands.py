#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for CLI commands.

This module contains unit tests for the Click CLI commands.
"""

from click.testing import CliRunner

from avd_cli.cli.main import cli


class TestCliMain:
    """Test cases for main CLI group."""

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test that CLI help is displayed correctly.

        Given: No prior context
        When: Running CLI with --help flag
        Then: Help text is displayed with zero exit code
        """
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "AVD CLI" in result.output
        assert "generate" in result.output
        assert "validate" in result.output
        assert "info" in result.output

    def test_cli_version(self, runner: CliRunner) -> None:
        """Test that version is displayed correctly.

        Given: No prior context
        When: Running CLI with --version flag
        Then: Version string is displayed
        """
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "avd-cli" in result.output.lower()


class TestGenerateCommand:
    """Test cases for generate command."""

    def test_generate_help(self, runner: CliRunner) -> None:
        """Test generate command help.

        Given: No prior context
        When: Running generate --help
        Then: Help text shows command group with subcommands
        """
        result = runner.invoke(cli, ["generate", "--help"])

        assert result.exit_code == 0
        assert "all" in result.output  # Subcommand
        assert "configs" in result.output  # Subcommand
        assert "docs" in result.output  # Subcommand
        assert "tests" in result.output  # Subcommand

    def test_generate_missing_required_options(self, runner: CliRunner) -> None:
        """Test generate all command fails without required options.

        Given: No command options provided
        When: Running generate all command
        Then: Command fails with error about missing options
        """
        result = runner.invoke(cli, ["generate", "all"])

        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output or "required" in result.output.lower()


class TestValidateCommand:
    """Test cases for validate command."""

    def test_validate_help(self, runner: CliRunner) -> None:
        """Test validate command help.

        Given: No prior context
        When: Running validate --help
        Then: Help text includes all options
        """
        result = runner.invoke(cli, ["validate", "--help"])

        assert result.exit_code == 0
        assert "--inventory-path" in result.output

    def test_validate_missing_required_options(self, runner: CliRunner) -> None:
        """Test validate command fails without required options.

        Given: No command options provided
        When: Running validate command
        Then: Command fails with error about missing options
        """
        result = runner.invoke(cli, ["validate"])

        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output


class TestInfoCommand:
    """Test cases for info command."""

    def test_info_help(self, runner: CliRunner) -> None:
        """Test info command help.

        Given: No prior context
        When: Running info --help
        Then: Help text includes all options
        """
        result = runner.invoke(cli, ["info", "--help"])

        assert result.exit_code == 0
        assert "--inventory-path" in result.output
        assert "--format" in result.output

    def test_info_missing_required_options(self, runner: CliRunner) -> None:
        """Test info command fails without required options.

        Given: No command options provided
        When: Running info command
        Then: Command fails with error about missing options
        """
        result = runner.invoke(cli, ["info"])

        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output
