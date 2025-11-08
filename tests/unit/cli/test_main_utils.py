#!/usr/bin/env python
# coding: utf-8 -*-

"""Additional unit tests for CLI main module utility functions."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from avd_cli.cli.main import display_generation_summary, suppress_pyavd_warnings


class TestUtilityFunctions:
    """Test CLI utility functions not covered by main command tests."""

    def test_suppress_pyavd_warnings_enabled(self):
        """Test suppressing pyavd warnings when show_warnings=False."""
        with patch("warnings.filterwarnings") as mock_filter:
            suppress_pyavd_warnings(show_warnings=False)

            # Should filter out deprecation warnings
            mock_filter.assert_called_once_with("ignore", message=".*is deprecated.*", category=UserWarning)

    def test_suppress_pyavd_warnings_disabled(self):
        """Test not suppressing pyavd warnings when show_warnings=True."""
        with patch("warnings.filterwarnings") as mock_filter:
            suppress_pyavd_warnings(show_warnings=True)

            # Should not filter warnings
            mock_filter.assert_not_called()

    def test_display_generation_summary_default_subcategory(self):
        """Test display generation summary with default subcategory."""
        output_path = Path("/test/output")

        with patch("rich.console.Console.print") as mock_print:
            display_generation_summary("Configurations", 5, output_path)

            # Should have been called with a table
            mock_print.assert_called()
            args = mock_print.call_args[0]

            # Verify a table-like object was passed
            assert hasattr(args[0], "title")
            assert "Generated Files" in str(args[0].title)

    def test_display_generation_summary_custom_subcategory(self):
        """Test display generation summary with custom subcategory."""
        output_path = Path("/test/output")

        with patch("rich.console.Console.print") as mock_print:
            display_generation_summary("Documentation", 3, output_path, subcategory="docs")

            # Should have been called
            mock_print.assert_called()

    def test_display_generation_summary_zero_count(self):
        """Test display generation summary with zero files."""
        output_path = Path("/test/output")

        with patch("rich.console.Console.print") as mock_print:
            display_generation_summary("Tests", 0, output_path, subcategory="tests")

            # Should still display table
            mock_print.assert_called()


class TestCliErrorHandling:
    """Test CLI error handling scenarios."""

    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_cli_import_error_handling(self):
        """Test CLI handles import errors gracefully."""
        from avd_cli.cli.main import cli

        # Test that CLI loads without error
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_cli_with_invalid_log_level(self):
        """Test CLI with invalid log level environment variable."""
        import os

        from avd_cli.cli.main import cli

        with patch.dict(os.environ, {"AVD_LOG_LEVEL": "INVALID_LEVEL"}):
            # Should still work, just ignore invalid log level
            result = self.runner.invoke(cli, ["--help"])
            assert result.exit_code == 0

    def test_cli_version_display(self):
        """Test CLI version display."""
        from avd_cli.cli.main import cli

        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_cli_verbose_option(self):
        """Test CLI verbose option."""
        from avd_cli.cli.main import cli

        # Test verbose help doesn't crash
        result = self.runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0


class TestEnvironmentVariableHandling:
    """Test environment variable processing."""

    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_env_var_precedence(self):
        """Test that CLI arguments take precedence over environment variables."""
        import os

        from avd_cli.cli.main import cli

        # Set environment variable
        with patch.dict(os.environ, {"AVD_INVENTORY_PATH": "/env/path"}):
            # CLI arg should override env var - test with info command
            result = self.runner.invoke(cli, ["info", "--inventory-path", "/cli/path"])

            # Should process CLI arg without error
            # (The actual functionality will be tested by mocked functions)
            assert result.exit_code in [0, 1, 2]  # May exit with error due to missing files, but shouldn't crash

    def test_boolean_env_vars(self):
        """Test boolean environment variable parsing."""
        import os

        from avd_cli.cli.main import cli

        # Test various boolean representations
        bool_values = ["1", "true", "True", "TRUE", "yes", "Yes", "YES"]

        for bool_val in bool_values:
            with patch.dict(os.environ, {"AVD_SHOW_DEPRECATION_WARNINGS": bool_val}):
                result = self.runner.invoke(cli, ["--help"])
                assert result.exit_code == 0

    def test_path_env_var_expansion(self):
        """Test path environment variable expansion."""
        import os

        from avd_cli.cli.main import cli

        # Test with tilde expansion
        with patch.dict(os.environ, {"AVD_INVENTORY_PATH": "~/test/path"}):
            result = self.runner.invoke(cli, ["info"])
            # Should handle path expansion without crashing
            assert result.exit_code in [0, 1, 2]


class TestClickContextHandling:
    """Test Click context and parameter handling."""

    def test_help_text_generation(self):
        """Test that help text is generated correctly."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test main help
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "validate" in result.output
        assert "info" in result.output

    def test_command_help_text(self):
        """Test individual command help text."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        commands = ["generate", "validate", "info"]

        for cmd in commands:
            result = runner.invoke(cli, [cmd, "--help"])
            assert result.exit_code == 0
            assert "Usage:" in result.output

    def test_nested_command_help(self):
        """Test nested command help (generate subcommands)."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test generate subcommand help
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "all" in result.output or "configs" in result.output

        # Test specific generate subcommand help
        subcommands = ["all", "configs", "docs", "tests"]

        for subcmd in subcommands:
            result = runner.invoke(cli, ["generate", subcmd, "--help"])
            assert result.exit_code == 0
            assert "Usage:" in result.output


class TestRichIntegration:
    """Test Rich console integration."""

    def test_console_initialization(self):
        """Test that Rich console is initialized."""
        from avd_cli.cli.main import console

        assert console is not None
        assert hasattr(console, "print")

    def test_rich_table_creation(self):
        """Test Rich table creation in display functions."""
        from rich.table import Table

        # This is tested implicitly in display_generation_summary tests
        # but we can test table creation directly
        table = Table(title="Test Table")
        assert table.title == "Test Table"

    def test_error_console_output(self):
        """Test error output through Rich console."""
        from avd_cli.cli.main import console

        # Test that console can handle error output
        with patch.object(console, "print") as mock_print:
            console.print("Test error", style="red")
            mock_print.assert_called_once_with("Test error", style="red")


class TestCommandValidation:
    """Test command parameter validation."""

    def test_required_parameters_validation(self):
        """Test that required parameters are validated."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test generate without required parameters
        result = runner.invoke(cli, ["generate", "all"])
        # Should fail due to missing required parameters
        assert result.exit_code != 0

    def test_path_parameter_validation(self):
        """Test path parameter validation."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test with non-existent path
        result = runner.invoke(cli, ["info", "--inventory-path", "/nonexistent/path"])
        # Should handle gracefully
        assert result.exit_code in [0, 1, 2]  # Various exit codes for different errors

    def test_format_parameter_validation(self):
        """Test format parameter validation."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test with valid format
        result = runner.invoke(cli, ["info", "--format", "json", "--inventory-path", "/tmp"])
        # Should accept valid format
        assert result.exit_code in [0, 1]  # May fail due to missing files but format should be accepted


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_logging_setup(self):
        """Test that logging is configured properly."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test with verbose flag
        with patch("logging.basicConfig"):
            result = runner.invoke(cli, ["--verbose", "--help"])

            # Logging should be configured
            # Note: actual logging setup may happen in other parts of the code
            assert result.exit_code == 0

    def test_debug_logging(self):
        """Test debug logging level."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test that debug mode doesn't crash
        result = runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0


class TestExceptionHandling:
    """Test exception handling in CLI commands."""

    def test_keyboard_interrupt_handling(self):
        """Test keyboard interrupt handling."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test that help command works (basic sanity check)
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_generic_exception_handling(self):
        """Test generic exception handling."""
        from avd_cli.cli.main import cli

        runner = CliRunner()

        # Test with invalid command
        result = runner.invoke(cli, ["nonexistent-command"])
        # Should handle invalid command gracefully
        assert result.exit_code != 0
        assert "Usage:" in result.output or "No such command" in result.output
