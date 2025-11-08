#!/usr/bin/env python
# coding: utf-8 -*-

"""Test utilities for integration tests.

This module provides utilities to help with integration testing,
particularly for handling Rich console output in Click tests.
"""

from contextlib import contextmanager
from io import StringIO
from unittest.mock import Mock, patch
from typing import Generator


@contextmanager
def mock_rich_console() -> Generator[Mock, None, None]:
    """Mock Rich console to prevent I/O issues in Click tests.

    This context manager replaces Rich console operations with mocks
    to avoid "I/O operation on closed file" errors when testing CLI
    commands that use Rich for output formatting.

    Yields
    ------
    Mock
        Mocked console object that captures method calls
    """
    mock_console = Mock()
    mock_console.print = Mock()
    mock_console.rule = Mock()
    mock_console.status = Mock()

    # Mock the status context manager
    mock_status = Mock()
    mock_status.__enter__ = Mock(return_value=mock_status)
    mock_status.__exit__ = Mock(return_value=None)
    mock_console.status.return_value = mock_status

    with patch('avd_cli.cli.main.console', mock_console):
        with patch('rich.console.Console', return_value=mock_console):
            yield mock_console


@contextmanager
def capture_rich_output() -> Generator[StringIO, None, None]:
    """Capture Rich console output for testing.

    This context manager redirects Rich console output to a StringIO
    buffer that can be safely accessed in tests.

    Yields
    ------
    StringIO
        Buffer containing captured output
    """
    captured_output = StringIO()

    def mock_print(*args, **kwargs):
        print(*args, file=captured_output, **kwargs)

    mock_console = Mock()
    mock_console.print = mock_print
    mock_console.rule = Mock()
    mock_console.status = Mock()

    # Mock the status context manager
    mock_status = Mock()
    mock_status.__enter__ = Mock(return_value=mock_status)
    mock_status.__exit__ = Mock(return_value=None)
    mock_console.status.return_value = mock_status

    with patch('avd_cli.cli.main.console', mock_console):
        with patch('rich.console.Console', return_value=mock_console):
            yield captured_output


class MockResult:
    """Mock result class for Click testing with I/O issues."""

    def __init__(self, exit_code=0, exception=None, output=""):
        self.exit_code = exit_code
        self.output = output
        self.stdout_bytes = b""
        self.stderr_bytes = b""
        self.exception = exception
        self.exc_info = None


def _handle_io_error(runner, cli, args, **kwargs):
    """Handle I/O operation errors during CLI invocation."""
    try:
        # Run without rich mocking to get actual exit code
        temp_result = runner.invoke(
            cli, args, standalone_mode=False, catch_exceptions=True, **kwargs
        )

        # Try to capture some output if available
        output = ""
        if hasattr(temp_result, 'output') and temp_result.output:
            try:
                output = str(temp_result.output)
            except Exception:
                output = ""

        return MockResult(temp_result.exit_code, temp_result.exception, output)
    except Exception as ex:
        # If we can't even run the command, return failure
        return MockResult(1, ex, str(ex))


def safe_click_invoke(runner, cli, args, **kwargs):
    """Safely invoke Click CLI command with Rich console mocking.

    This function wraps Click's invoke method with Rich console mocking
    to prevent I/O stream issues during testing.

    Parameters
    ----------
    runner : CliRunner
        Click test runner
    cli : click.Command
        CLI command to invoke
    args : list
        Command arguments
    **kwargs
        Additional arguments to pass to invoke

    Returns
    -------
    Result
        Click test result, with any I/O errors handled gracefully
    """
    with mock_rich_console():
        try:
            return runner.invoke(cli, args, **kwargs)
        except ValueError as e:
            if "I/O operation on closed file" in str(e):
                return _handle_io_error(runner, cli, args, **kwargs)
            raise
