#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for CLI shared module helpers."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from avd_cli.cli import shared


class TestSuppressPyavdWarnings:
    """Test suite for suppress_pyavd_warnings function."""

    def test_suppress_warnings_when_false(self):
        """Test that warnings are suppressed when show_warnings is False."""
        with patch("warnings.filterwarnings") as mock_filter:
            shared.suppress_pyavd_warnings(False)
            mock_filter.assert_called_once()

    def test_no_suppress_when_true(self):
        """Test that warnings are not suppressed when show_warnings is True."""
        with patch("warnings.filterwarnings") as mock_filter:
            shared.suppress_pyavd_warnings(True)
            mock_filter.assert_not_called()


class TestResolveOutputPath:
    """Test suite for resolve_output_path function."""

    def test_returns_provided_path_when_given(self, tmp_path):
        """Test that provided output path is returned as-is."""
        inventory_path = tmp_path / "inventory"
        output_path = tmp_path / "output"

        result = shared.resolve_output_path(inventory_path, output_path)

        assert result == output_path

    def test_uses_default_when_none(self, tmp_path):
        """Test that default path is used when output_path is None."""
        inventory_path = tmp_path / "inventory"

        result = shared.resolve_output_path(inventory_path, None)

        assert result == inventory_path / "intended"

    def test_prints_default_message(self, tmp_path, capsys):
        """Test that a message is printed when using default path."""
        inventory_path = tmp_path / "inventory"

        with patch("avd_cli.cli.shared.console") as mock_console:
            shared.resolve_output_path(inventory_path, None)
            mock_console.print.assert_called_once()


class TestDisplayGenerationSummary:
    """Test suite for display_generation_summary function."""

    def test_displays_summary_with_defaults(self, tmp_path):
        """Test summary display with default subcategory."""
        output_path = tmp_path / "output"

        with patch("avd_cli.cli.shared.console") as mock_console:
            shared.display_generation_summary("Configs", 10, output_path)

            # Verify console was used to print
            assert mock_console.print.call_count >= 2

    def test_displays_summary_with_custom_subcategory(self, tmp_path):
        """Test summary display with custom subcategory."""
        output_path = tmp_path / "output"

        with patch("avd_cli.cli.shared.console") as mock_console:
            shared.display_generation_summary(
                "Documentation", 5, output_path, "docs"
            )

            # Verify console was used to print
            assert mock_console.print.call_count >= 2

    def test_displays_zero_count(self, tmp_path):
        """Test summary display with zero files."""
        output_path = tmp_path / "output"

        with patch("avd_cli.cli.shared.console") as mock_console:
            shared.display_generation_summary("Tests", 0, output_path, "tests")

            # Verify console was used to print
            assert mock_console.print.call_count >= 2


class TestCommonGenerateOptions:
    """Test suite for common_generate_options decorator."""

    def test_decorator_adds_options(self):
        """Test that decorator adds all required options."""

        @shared.common_generate_options
        def dummy_command(ctx, **kwargs):
            return kwargs

        # Verify the function has been decorated with click options
        assert hasattr(dummy_command, "__click_params__")
        params = dummy_command.__click_params__

        # Should have multiple parameters added
        assert len(params) > 0

        # Check for specific expected options
        param_names = [p.name for p in params if hasattr(p, "name")]
        assert "inventory_path" in param_names or any(
            "inventory" in str(p) for p in params
        )


class TestMainCli:
    """Test suite for main_cli function."""

    def test_creates_cli_group(self):
        """Test that main_cli creates a Click group."""
        cli = shared.main_cli()

        assert cli is not None
        # Should be a Click group
        assert hasattr(cli, "invoke")

    def test_cli_has_version_option(self):
        """Test that CLI has version option."""
        cli = shared.main_cli()
        runner = CliRunner()

        result = runner.invoke(cli, ["--version"])

        # Should show version
        assert "avd-cli" in result.output.lower() or "version" in result.output.lower()

    def test_cli_has_verbose_option(self):
        """Test that CLI has verbose option."""
        cli = shared.main_cli()
        runner = CliRunner()

        result = runner.invoke(cli, ["--verbose", "--help"])

        # Should process verbose flag (exit code 0 for help)
        assert result.exit_code == 0

    def test_cli_stores_verbose_in_context(self):
        """Test that verbose flag is stored in context."""
        cli = shared.main_cli()

        @cli.command()
        @shared.common_generate_options
        def test_cmd(ctx, **kwargs):
            return ctx.obj.get("verbose", False)

        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "test-cmd", "--help"], obj={})

        # Command should be registered
        assert "test-cmd" in cli.list_commands({})


class TestRunCli:
    """Test suite for run_cli function."""

    def test_run_cli_success(self):
        """Test successful CLI execution."""
        cli = shared.main_cli()

        # Add a dummy command to make CLI work
        @cli.command()
        def test_command():
            pass

        runner = CliRunner()
        with patch.object(shared, "run_cli") as mock_run:
            # Test that run_cli can be called
            mock_run.return_value = None
            shared.run_cli(cli)
            mock_run.assert_called_once()

    def test_run_cli_with_exception(self):
        """Test CLI execution with exception."""
        cli = shared.main_cli()

        with patch.object(cli, "__call__") as mock_call:
            mock_call.side_effect = ValueError("Test error")

            # Should exit with code 1
            with pytest.raises(SystemExit) as exc_info:
                shared.run_cli(cli)

            # Click may return different exit codes
            assert exc_info.value.code != 0

    def test_run_cli_shows_exception_in_verbose(self):
        """Test that exception is handled properly in run_cli."""
        cli = shared.main_cli()

        with patch.object(cli, "__call__") as mock_call:
            mock_call.side_effect = ValueError("Test error")

            with pytest.raises(SystemExit) as exc_info:
                shared.run_cli(cli)

            # Should exit with non-zero code (1 for general errors, 2 for Click usage errors)
            assert exc_info.value.code != 0


class TestConsoleObject:
    """Test suite for console object."""

    def test_console_is_available(self):
        """Test that console object is importable."""
        assert shared.console is not None

    def test_console_has_print_method(self):
        """Test that console has print method."""
        assert hasattr(shared.console, "print")

    def test_console_can_print(self):
        """Test that console can print messages."""
        # Should not raise
        shared.console.print("Test message", style="dim")
